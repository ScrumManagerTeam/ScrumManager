from app import app
from models import db, User, Project, PBI, Sprint, Task, EffortLog, AuditLog
from datetime import date, datetime, timedelta


def seed():
    with app.app_context():
        # Clear existing data (audit logs first — they reference users)
        AuditLog.query.delete()
        EffortLog.query.delete()
        Task.query.delete()
        PBI.query.delete()
        Sprint.query.delete()
        Project.query.delete()
        User.query.delete()
        db.session.commit()

        # Create users
        dev1 = User(username="alice", role="developer")
        dev1.set_password("password123")

        dev2 = User(username="bob", role="developer")
        dev2.set_password("password123")

        client = User(username="carol", role="client")
        client.set_password("password123")

        db.session.add_all([dev1, dev2, client])
        db.session.commit()

        # Create project
        project = Project(
            name="Demo Scrum Project",
            description="A demo project to showcase the ScrumManager app."
        )
        db.session.add(project)
        db.session.commit()

        # Create PBIs
        pbis = [
            PBI(title="User login page", priority="H", effort=5.0, status="Complete", project_id=project.id),
            PBI(title="Home page UI", priority="H", effort=8.0, status="Complete", project_id=project.id),
            PBI(title="Product backlog view", priority="M", effort=5.0, status="Complete", project_id=project.id),
            PBI(title="Sprint planning tool", priority="M", effort=8.0, status="Incomplete", project_id=project.id),
            PBI(title="Burndown chart", priority="L", effort=6.0, status="Incomplete", project_id=project.id),
            PBI(title="Email notifications", priority="L", effort=4.0, status="Incomplete", project_id=project.id),
        ]
        db.session.add_all(pbis)
        db.session.commit()

        # Create sprints — sprint 1 ran 20..7 days ago, sprint 2 started 5 days ago
        now = datetime.now()
        sprint1 = Sprint(capacity=18.0, status="Complete", project_id=project.id, created_at=now - timedelta(days=20))
        sprint2 = Sprint(capacity=14.0, status="Active", project_id=project.id, created_at=now - timedelta(days=5))
        db.session.add_all([sprint1, sprint2])
        db.session.commit()

        # Assign PBIs to sprints
        pbis[0].sprint_id = sprint1.id
        pbis[1].sprint_id = sprint1.id
        pbis[2].sprint_id = sprint1.id
        pbis[3].sprint_id = sprint2.id
        pbis[4].sprint_id = sprint2.id
        db.session.commit()

        # Create tasks — estimates add up to each PBI's effort
        tasks = [
            Task(title="Design login form", estimated_effort=2.0, status="Done", pbi_id=pbis[0].id),
            Task(title="Implement auth logic", estimated_effort=3.0, status="Done", pbi_id=pbis[0].id),
            Task(title="Build homepage layout", estimated_effort=5.0, status="Done", pbi_id=pbis[1].id),
            Task(title="Add navigation bar", estimated_effort=3.0, status="Done", pbi_id=pbis[1].id),
            Task(title="Build backlog table", estimated_effort=3.0, status="Done", pbi_id=pbis[2].id),
            Task(title="Add column sorting", estimated_effort=2.0, status="Done", pbi_id=pbis[2].id),
            Task(title="Write unit tests", estimated_effort=3.0, status="Not Started", pbi_id=pbis[3].id),
            Task(title="Sprint capacity logic", estimated_effort=5.0, status="In Progress", pbi_id=pbis[3].id),
            Task(title="Burndown API endpoint", estimated_effort=3.0, status="In Progress", pbi_id=pbis[4].id),
            Task(title="Burndown chart UI", estimated_effort=3.0, status="Not Started", pbi_id=pbis[4].id),
        ]
        db.session.add_all(tasks)
        db.session.commit()

        # Log effort inside each sprint's window — dates relative to today so the burndown chart works
        today = date.today()
        effort = [
            # Sprint 1 (all 18h done)
            (tasks[0], 19, 2.0), (tasks[1], 17, 3.0), (tasks[2], 15, 5.0),
            (tasks[3], 13, 3.0), (tasks[4], 11, 3.0), (tasks[5], 9, 2.0),
            # Sprint 2 (6.5h of 14h done so far)
            (tasks[7], 4, 3.0), (tasks[7], 2, 1.5), (tasks[8], 1, 2.0),
        ]
        logs = []
        for task, days_ago, hours in effort:
            logs.append(EffortLog(task_id=task.id, date=today - timedelta(days=days_ago), hours_spent=hours))
            task.actual_effort = (task.actual_effort or 0) + hours
        db.session.add_all(logs)
        db.session.commit()

        print("✅ Database seeded successfully!")
        print(f"   Users: alice, bob (developers), carol (client) — all password: password123")
        print(f"   Project: {project.name}")
        print(f"   PBIs: {len(pbis)}, Sprints: 2, Tasks: {len(tasks)}")


if __name__ == "__main__":
    seed()