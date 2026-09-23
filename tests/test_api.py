from datetime import date, datetime, timedelta
from models import db, PBI, Sprint, Task, EffortLog


def get_token(client, username="dev_user", password="devpass123"):
    response = client.post("/api/auth/login", json={
        "username": username,
        "password": password,
    })
    return response.json["access_token"]


# --- Auth tests ---
def test_login_returns_token(client, seeded_users):
    response = client.post("/api/auth/login", json={
        "username": "dev_user",
        "password": "devpass123",
    })
    assert response.status_code == 200
    assert "access_token" in response.json
    assert response.json["role"] == "developer"


def test_login_wrong_password(client, seeded_users):
    response = client.post("/api/auth/login", json={
        "username": "dev_user",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


def test_login_missing_fields(client, seeded_users):
    response = client.post("/api/auth/login", json={"username": "dev_user"})
    assert response.status_code == 400


# --- PBI tests ---
def test_get_pbis_without_token(client, seeded_users):
    response = client.get("/api/pbis/")
    assert response.status_code == 401


def test_get_pbis_with_token(client, seeded_users):
    token = get_token(client)
    response = client.get("/api/pbis/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "pbis" in response.json
    assert "total" in response.json
    assert "page" in response.json


def test_get_pbis_pagination(client, seeded_users):
    token = get_token(client)
    response = client.get("/api/pbis/?page=1&per_page=2", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json["pbis"]) <= 2


def test_create_pbi(client, seeded_users, app):
    token = get_token(client)
    response = client.post("/api/pbis/", json={
        "title": "New API PBI",
        "priority": "H",
        "effort": 5.0,
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    assert response.json["title"] == "New API PBI"


def test_create_pbi_missing_title(client, seeded_users):
    token = get_token(client)
    response = client.post("/api/pbis/", json={
        "priority": "H",
        "effort": 5.0,
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400


def test_create_pbi_invalid_priority(client, seeded_users):
    token = get_token(client)
    response = client.post("/api/pbis/", json={
        "title": "Bad PBI",
        "priority": "X",
        "effort": 5.0,
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400


def test_get_pbi_not_found(client, seeded_users):
    token = get_token(client)
    response = client.get("/api/pbis/99999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


# --- Sprint tests ---
def test_get_sprints_with_token(client, seeded_users):
    token = get_token(client)
    response = client.get("/api/sprints/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "sprints" in response.json


def test_get_sprint_not_found(client, seeded_users):
    token = get_token(client)
    response = client.get("/api/sprints/99999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


# --- Task tests ---
def test_get_tasks_with_token(client, seeded_users):
    token = get_token(client)
    response = client.get("/api/tasks/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "tasks" in response.json


def test_get_task_not_found(client, seeded_users):
    token = get_token(client)
    response = client.get("/api/tasks/99999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404

# --- Reports tests ---
def make_sprint_with_effort(status="Active"):
    """Sprint started 3 days ago: one 10h PBI with a task and some effort logs."""
    today = date.today()
    sprint = Sprint(capacity=10.0, status=status, created_at=datetime.now() - timedelta(days=3))
    db.session.add(sprint)
    db.session.flush()
    pbi = PBI(title="Report PBI", priority="H", effort=10.0,
              status="Complete" if status == "Complete" else "Incomplete", sprint_id=sprint.id)
    db.session.add(pbi)
    db.session.flush()
    task = Task(title="Report task", estimated_effort=4.0, pbi_id=pbi.id)
    db.session.add(task)
    db.session.flush()
    db.session.add_all([
        EffortLog(task_id=task.id, date=today - timedelta(days=5), hours_spent=2.0),  # before the sprint
        EffortLog(task_id=task.id, date=today - timedelta(days=2), hours_spent=3.0),  # sprint day 2
        EffortLog(task_id=task.id, date=today, hours_spent=1.0),                      # sprint day 4
    ])
    db.session.commit()
    return sprint.id


def test_burndown_requires_token(client, seeded_users):
    response = client.get("/api/burndown/sprints/1/burndown")
    assert response.status_code == 401


def test_burndown_uses_pbi_effort_and_ignores_effort_before_sprint(client, seeded_users):
    sprint_id = make_sprint_with_effort()
    token = get_token(client)
    response = client.get(f"/api/burndown/sprints/{sprint_id}/burndown",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json
    assert data["days"] == ["Day 1", "Day 2", "Day 3", "Day 4"]
    assert data["ideal"][0] == 10.0
    # Starts at full PBI effort; the 2h logged before the sprint is not counted
    assert data["actual"] == [10.0, 7.0, 7.0, 6.0]


def test_burndown_not_found(client, seeded_users):
    token = get_token(client)
    response = client.get("/api/burndown/sprints/99999/burndown",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_velocity_matches_burndown_scope(client, seeded_users):
    sprint_id = make_sprint_with_effort(status="Complete")
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    velocity = client.get("/api/velocity/sprints/velocity", headers=headers).json
    burndown = client.get(f"/api/burndown/sprints/{sprint_id}/burndown", headers=headers).json
    assert velocity == [{"sprint_id": sprint_id, "sprint_label": f"Sprint #{sprint_id}", "effort_completed": 10.0}]
    assert burndown["ideal"][0] == velocity[0]["effort_completed"]
