from app import app
from models import db, User, Project, PBI, Sprint, Task, EffortLog
from datetime import date


def seed():
    with app.app_context():
        # Clear existing data
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

        # Create sprints
        sprint1 = Sprint(capacity=18.0, status="Complete", project_id=project.id)
        sprint2 = Sprint(capacity=14.0, status="Active", project_id=project.id)
        db.session.add_all([sprint1, sprint2])
        db.session.commit()

        # Assign PBIs to sprints
        pbis[0].sprint_id = sprint1.id
        pbis[1].sprint_id = sprint1.id
        pbis[2].sprint_id = sprint1.id
        pbis[3].sprint_id = sprint2.id
        pbis[4].sprint_id = sprint2.id
        db.session.commit()

        # Create tasks
        tasks = [
            Task(title="Design login form", estimated_effort=2.0, status="Done", pbi_id=pbis[0].id),
            Task(title="Implement auth logic", estimated_effort=3.0, status="Done", pbi_id=pbis[0].id),
            Task(title="Build homepage layout", estimated_effort=4.0, status="Done", pbi_id=pbis[1].id),
            Task(title="Add navigation bar", estimated_effort=2.0, status="Done", pbi_id=pbis[1].id),
            Task(title="Write unit tests", estimated_effort=2.0, status="Not Started", pbi_id=pbis[3].id),
            Task(title="Sprint capacity logic", estimated_effort=3.0, status="In Progress", pbi_id=pbis[3].id),
        ]
        db.session.add_all(tasks)
        db.session.commit()

        # Log some effort — dates relative to today so burndown chart works
        from datetime import date, timedelta
        today = date.today()
        logs = [
            EffortLog(task_id=tasks[0].id, date=today - timedelta(days=6), hours_spent=2.0),
            EffortLog(task_id=tasks[1].id, date=today - timedelta(days=5), hours_spent=3.0),
            EffortLog(task_id=tasks[2].id, date=today - timedelta(days=4), hours_spent=4.0),
            EffortLog(task_id=tasks[3].id, date=today - timedelta(days=3), hours_spent=2.0),
            EffortLog(task_id=tasks[5].id, date=today - timedelta(days=1), hours_spent=1.5),
        ]
        db.session.add_all(logs)
        db.session.commit()

        print("✅ Database seeded successfully!")
        print(f"   Users: alice, bob (developers), carol (client) — all password: password123")
        print(f"   Project: {project.name}")
        print(f"   PBIs: {len(pbis)}, Sprints: 2, Tasks: {len(tasks)}")


if __name__ == "__main__":
    seed()