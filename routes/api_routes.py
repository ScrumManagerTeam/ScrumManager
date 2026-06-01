from flask import Blueprint, request
from flask_restx import Api, Resource, fields
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from models import db, PBI, Sprint, Task, User

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp, doc="/docs", title="ScrumManager API", version="1.0",
          description="REST API for ScrumManager",
          authorizations={
              "Bearer": {
                  "type": "apiKey",
                  "in": "header",
                  "name": "Authorization",
                  "description": "Enter: Bearer <your_token>"
              }
          },
          security="Bearer")

# --- Namespaces ---
auth_ns = api.namespace("auth", description="Authentication")
pbi_ns = api.namespace("pbis", description="Product Backlog Items")
sprint_ns = api.namespace("sprints", description="Sprints")
task_ns = api.namespace("tasks", description="Tasks")

# --- Models ---
login_model = api.model("Login", {
    "username": fields.String(required=True),
    "password": fields.String(required=True),
})

token_model = api.model("Token", {
    "access_token": fields.String,
    "role": fields.String,
})

pbi_input_model = api.model("PBIInput", {
    "title": fields.String(required=True, description="PBI title"),
    "priority": fields.String(required=True, description="H, M, or L"),
    "effort": fields.Float(required=True, description="Effort in hours"),
})

pbi_model = api.model("PBI", {
    "id": fields.Integer,
    "title": fields.String,
    "priority": fields.String,
    "effort": fields.Float,
    "status": fields.String,
    "sprint_id": fields.Integer,
})

paginated_pbi_model = api.model("PaginatedPBIs", {
    "pbis": fields.List(fields.Nested(pbi_model)),
    "total": fields.Integer,
    "page": fields.Integer,
    "per_page": fields.Integer,
    "pages": fields.Integer,
})

sprint_model = api.model("Sprint", {
    "id": fields.Integer,
    "capacity": fields.Float,
    "status": fields.String,
})

paginated_sprint_model = api.model("PaginatedSprints", {
    "sprints": fields.List(fields.Nested(sprint_model)),
    "total": fields.Integer,
    "page": fields.Integer,
    "per_page": fields.Integer,
    "pages": fields.Integer,
})

task_model = api.model("Task", {
    "id": fields.Integer,
    "title": fields.String,
    "estimated_effort": fields.Float,
    "actual_effort": fields.Float,
    "status": fields.String,
    "pbi_id": fields.Integer,
})

paginated_task_model = api.model("PaginatedTasks", {
    "tasks": fields.List(fields.Nested(task_model)),
    "total": fields.Integer,
    "page": fields.Integer,
    "per_page": fields.Integer,
    "pages": fields.Integer,
})

# --- Auth Endpoints ---
@auth_ns.route("/login")
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(token_model)
    def post(self):
        """Login and get a JWT token"""
        data = api.payload
        if not data or "username" not in data or "password" not in data:
            api.abort(400, "Username and password are required")
        user = User.query.filter_by(username=data["username"]).first()
        if user and user.check_password(data["password"]):
            token = create_access_token(identity=str(user.id))
            return {"access_token": token, "role": user.role}
        api.abort(401, "Invalid username or password")

# --- PBI Endpoints ---
@pbi_ns.route("/")
class PBIList(Resource):
    @jwt_required()
    @pbi_ns.marshal_with(paginated_pbi_model)
    def get(self):
        """Get all PBIs with pagination"""
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        per_page = min(per_page, 100)
        pagination = PBI.query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "pbis": pagination.items,
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
        }

    @jwt_required()
    @pbi_ns.expect(pbi_input_model)
    @pbi_ns.marshal_with(pbi_model, code=201)
    def post(self):
        """Create a new PBI"""
        data = api.payload
        if not data.get("title", "").strip():
            api.abort(400, "title is required")
        if data.get("priority") not in ["H", "M", "L"]:
            api.abort(400, "priority must be H, M, or L")
        if not data.get("effort") or data["effort"] <= 0:
            api.abort(400, "effort must be a positive number")
        pbi = PBI(
            title=data["title"].strip(),
            priority=data["priority"],
            effort=data["effort"],
            status="Incomplete"
        )
        db.session.add(pbi)
        db.session.commit()
        return pbi, 201

@pbi_ns.route("/<int:pbi_id>")
class PBIItem(Resource):
    @jwt_required()
    @pbi_ns.marshal_with(pbi_model)
    def get(self, pbi_id):
        """Get a single PBI by ID"""
        pbi = PBI.query.get(pbi_id)
        if not pbi:
            api.abort(404, f"PBI {pbi_id} not found")
        return pbi

# --- Sprint Endpoints ---
sprint_input_model = api.model("SprintInput", {
    "capacity": fields.Float(required=True, description="Sprint capacity in hours"),
})

sprint_create_model = api.model("SprintCreate", {
    "capacity": fields.Float(required=True),
    "pbi_ids": fields.List(fields.Integer, required=True),
})

proposed_pbi_model = api.model("ProposedPBI", {
    "id": fields.Integer,
    "title": fields.String,
    "priority": fields.String,
    "effort": fields.Float,
})

proposal_model = api.model("Proposal", {
    "proposed": fields.List(fields.Nested(proposed_pbi_model)),
    "total_effort": fields.Float,
    "capacity": fields.Float,
    "error": fields.String,
})

@sprint_ns.route("/")
class SprintList(Resource):
    @jwt_required()
    @sprint_ns.marshal_with(paginated_sprint_model)
    def get(self):
        """Get all sprints with pagination"""
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        per_page = min(per_page, 100)
        pagination = Sprint.query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "sprints": pagination.items,
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
        }

@sprint_ns.route("/propose")
class SprintPropose(Resource):
    @jwt_required()
    @sprint_ns.expect(sprint_input_model)
    @sprint_ns.marshal_with(proposal_model)
    def post(self):
        """Propose a sprint based on capacity"""
        data = api.payload
        capacity = data.get("capacity")
        if not capacity or capacity <= 0:
            api.abort(400, "capacity must be a positive number")
        pbis = PBI.query.filter_by(sprint_id=None, status="Incomplete").all()
        if not pbis:
            return {"proposed": [], "total_effort": 0, "capacity": capacity, "error": "No items available"}
        priority_rank = {"H": 0, "M": 1, "L": 2}
        pbis.sort(key=lambda p: (priority_rank.get(p.priority, 9), p.effort))
        selected = []
        remaining = capacity
        for pbi in pbis:
            if pbi.effort <= remaining:
                selected.append({"id": pbi.id, "title": pbi.title, "priority": pbi.priority, "effort": pbi.effort})
                remaining -= pbi.effort
        if not selected:
            smallest = min(p.effort for p in pbis)
            return {"proposed": [], "total_effort": 0, "capacity": capacity,
                    "error": f"No items fit. Smallest item requires {smallest} hours."}
        total = sum(p["effort"] for p in selected)
        return {"proposed": selected, "total_effort": total, "capacity": capacity, "error": None}


@sprint_ns.route("/create")
class SprintCreate(Resource):
    @jwt_required()
    @sprint_ns.expect(sprint_create_model)
    @sprint_ns.marshal_with(sprint_model, code=201)
    def post(self):
        """Create a sprint and assign PBIs to it"""
        data = api.payload
        capacity = data.get("capacity")
        pbi_ids = data.get("pbi_ids", [])
        if not capacity or capacity <= 0:
            api.abort(400, "capacity must be a positive number")
        if not pbi_ids:
            api.abort(400, "pbi_ids cannot be empty")
        sprint = Sprint(capacity=capacity, status="Planned")
        db.session.add(sprint)
        db.session.flush()
        PBI.query.filter(PBI.id.in_(pbi_ids)).update(
            {"sprint_id": sprint.id}, synchronize_session="fetch"
        )
        db.session.commit()
        return sprint, 201


@sprint_ns.route("/<int:sprint_id>")
class SprintItem(Resource):
    @jwt_required()
    @sprint_ns.marshal_with(sprint_model)
    def get(self, sprint_id):
        """Get a single sprint by ID"""
        sprint = Sprint.query.get(sprint_id)
        if not sprint:
            api.abort(404, f"Sprint {sprint_id} not found")
        return sprint


@sprint_ns.route("/<int:sprint_id>/status")
class SprintStatus(Resource):
    @jwt_required()
    @sprint_ns.marshal_with(sprint_model)
    def post(self, sprint_id):
        """Advance sprint status: Planned → Active → Complete"""
        sprint = Sprint.query.get(sprint_id)
        if not sprint:
            api.abort(404, f"Sprint {sprint_id} not found")
        if sprint.status == "Planned":
            sprint.status = "Active"
        elif sprint.status == "Active":
            sprint.status = "Complete"
            _return_unfinished_pbis(sprint_id)
        else:
            api.abort(400, "Sprint is already complete")
        db.session.commit()
        return sprint


def _return_unfinished_pbis(sprint_id):
    from models import EffortLog, Task
    unfinished = PBI.query.filter_by(sprint_id=sprint_id).filter(PBI.status != "Complete").all()
    for pbi in unfinished:
        completed_effort = db.session.query(
            db.func.coalesce(db.func.sum(EffortLog.hours_spent), 0)
        ).join(Task, EffortLog.task_id == Task.id).filter(Task.pbi_id == pbi.id).scalar()
        pbi.sprint_id = None
        pbi.status = "Incomplete"
        pbi.effort = max(0, pbi.effort - completed_effort)
        
# --- Task Endpoints ---
@task_ns.route("/")
class TaskList(Resource):
    @jwt_required()
    @task_ns.marshal_with(paginated_task_model)
    def get(self):
        """Get all tasks with pagination"""
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        per_page = min(per_page, 100)
        pagination = Task.query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "tasks": pagination.items,
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
        }

@task_ns.route("/<int:task_id>")
class TaskItem(Resource):
    @jwt_required()
    @task_ns.marshal_with(task_model)
    def get(self, task_id):
        """Get a single task by ID"""
        task = Task.query.get(task_id)
        if not task:
            api.abort(404, f"Task {task_id} not found")
        return task
    
# --- Additional Task Endpoints ---

task_input_model = api.model("TaskInput", {
    "title": fields.String(required=True),
    "estimated_effort": fields.Float(required=True),
    "pbi_id": fields.Integer(required=True),
})

task_status_model = api.model("TaskStatus", {
    "status": fields.String(required=True, description="Not Started, In Progress, or Done"),
})

effort_log_input_model = api.model("EffortLogInput", {
    "hours_spent": fields.Float(required=True),
    "date": fields.String(required=True, description="YYYY-MM-DD"),
})

effort_log_model = api.model("EffortLog", {
    "id": fields.Integer,
    "task_id": fields.Integer,
    "date": fields.String,
    "hours_spent": fields.Float,
})

@task_ns.route("/by-pbi")
class TasksByPBI(Resource):
    @jwt_required()
    def get(self):
        """Get all tasks grouped by PBI (only PBIs in active/planned sprints)"""
        user_id = int(get_jwt_identity())
        pbis = PBI.query.filter(PBI.sprint_id.isnot(None)).all()
        result = []
        for pbi in pbis:
            tasks = Task.query.filter_by(pbi_id=pbi.id).all()
            all_done = len(tasks) > 0 and all(t.status == "Done" for t in tasks)
            result.append({
                "pbi_id": pbi.id,
                "pbi_title": pbi.title,
                "pbi_priority": pbi.priority,
                "pbi_status": pbi.status,
                "sprint_id": pbi.sprint_id,
                "all_done": all_done,
                "tasks": [t.to_dict() for t in tasks],
            })
        return result

@task_ns.route("/", methods=["POST"])
class TaskCreate(Resource):
    @jwt_required()
    @task_ns.expect(task_input_model)
    @task_ns.marshal_with(task_model, code=201)
    def post(self):
        """Create a new task under a PBI"""
        data = api.payload
        if not data.get("title", "").strip():
            api.abort(400, "title is required")
        if not data.get("estimated_effort") or data["estimated_effort"] <= 0:
            api.abort(400, "estimated_effort must be positive")
        pbi = PBI.query.get(data["pbi_id"])
        if not pbi:
            api.abort(404, "PBI not found")
        task = Task(
            title=data["title"].strip(),
            estimated_effort=data["estimated_effort"],
            pbi_id=data["pbi_id"],
            status="Not Started",
        )
        db.session.add(task)
        db.session.commit()
        return task, 201

@task_ns.route("/<int:task_id>/status")
class TaskStatus(Resource):
    @jwt_required()
    @task_ns.expect(task_status_model)
    @task_ns.marshal_with(task_model)
    def post(self, task_id):
        """Update task status"""
        task = Task.query.get(task_id)
        if not task:
            api.abort(404, f"Task {task_id} not found")
        status = api.payload.get("status")
        if status not in ["Not Started", "In Progress", "Done"]:
            api.abort(400, "status must be Not Started, In Progress, or Done")
        task.status = status
        db.session.commit()
        return task

@task_ns.route("/<int:task_id>/log-effort")
class TaskEffortLog(Resource):
    @jwt_required()
    @task_ns.expect(effort_log_input_model)
    @task_ns.marshal_with(effort_log_model, code=201)
    def post(self, task_id):
        """Log effort for a task"""
        from models import EffortLog
        from datetime import date as date_type
        task = Task.query.get(task_id)
        if not task:
            api.abort(404, f"Task {task_id} not found")
        data = api.payload
        if not data.get("hours_spent") or data["hours_spent"] <= 0:
            api.abort(400, "hours_spent must be positive")
        try:
            log_date = date_type.fromisoformat(data["date"])
        except ValueError:
            api.abort(400, "date must be YYYY-MM-DD format")
        log = EffortLog(task_id=task_id, date=log_date, hours_spent=data["hours_spent"])
        db.session.add(log)
        task.actual_effort = (task.actual_effort or 0) + data["hours_spent"]
        db.session.commit()
        return {"id": log.id, "task_id": log.task_id, "date": str(log.date), "hours_spent": log.hours_spent}, 201
    
    # --- Dashboard Stats ---
stats_model = api.model("Stats", {
    "open_pbis": fields.Integer,
    "tasks_done": fields.Integer,
    "tasks_total": fields.Integer,
    "effort_logged": fields.Float,
    "active_sprint_id": fields.Integer,
    "active_sprint_capacity": fields.Float,
    "velocity": fields.Float,
})

@api.namespace("stats", description="Dashboard stats").route("/")
class DashboardStats(Resource):
    @jwt_required()
    def get(self):
        """Get dashboard summary stats"""
        from models import EffortLog, Sprint as SprintModel
        open_pbis = PBI.query.filter_by(status="Incomplete").count()
        tasks_total = Task.query.count()
        tasks_done = Task.query.filter_by(status="Done").count()
        effort_logged = db.session.query(
            db.func.coalesce(db.func.sum(EffortLog.hours_spent), 0)
        ).scalar()
        active_sprint = SprintModel.query.filter_by(status="Active").first()
        last_complete = SprintModel.query.filter_by(status="Complete").order_by(SprintModel.id.desc()).first()
        velocity = 0.0
        if last_complete:
            done_pbis = PBI.query.filter_by(sprint_id=last_complete.id, status="Complete").all()
            velocity = sum(p.effort for p in done_pbis)
        return {
            "open_pbis": open_pbis,
            "tasks_done": tasks_done,
            "tasks_total": tasks_total,
            "effort_logged": float(effort_logged),
            "active_sprint_id": active_sprint.id if active_sprint else None,
            "active_sprint_capacity": active_sprint.capacity if active_sprint else 0,
            "velocity": velocity,
        }
    
burndown_ns = api.namespace("burndown", description="Burndown chart data")

@burndown_ns.route("/sprints/<int:sprint_id>/burndown")
class SprintBurndown(Resource):
    @jwt_required()
    def get(self, sprint_id):
        """Get burndown chart data for a sprint"""
        from models import Sprint as SprintModel, EffortLog
        import datetime

        sprint = SprintModel.query.get_or_404(sprint_id)
        pbis = PBI.query.filter_by(sprint_id=sprint_id).all()
        tasks = []
        for pbi in pbis:
            tasks.extend(Task.query.filter_by(pbi_id=pbi.id).all())

        total_effort = sum(t.estimated_effort or 0 for t in tasks)
        start_date = sprint.created_at.date()
        today = datetime.date.today()
        sprint_days = 14
        days = []
        ideal = []
        actual = []

        for i in range(sprint_days):
            day = start_date + datetime.timedelta(days=i)
            if day > today:
                break
            days.append(day.strftime("Day %d" % (i + 1)))
            ideal.append(round(total_effort * (1 - i / (sprint_days - 1)), 2))
            logged_so_far = db.session.query(
                db.func.coalesce(db.func.sum(EffortLog.hours_spent), 0)
            ).join(Task).filter(
                Task.id.in_([t.id for t in tasks]),
                EffortLog.date <= day
            ).scalar()
            actual.append(round(max(total_effort - float(logged_so_far), 0), 2))

        return {"days": days, "ideal": ideal, "actual": actual}


velocity_ns = api.namespace("velocity", description="Sprint velocity")

@velocity_ns.route("/sprints/velocity")
class SprintVelocity(Resource):
    @jwt_required()
    def get(self):
        """Get velocity for all completed sprints"""
        from models import Sprint as SprintModel
        sprints = SprintModel.query.filter_by(status="Complete").order_by(SprintModel.id).all()
        result = []
        for sprint in sprints:
            done_pbis = PBI.query.filter_by(sprint_id=sprint.id, status="Complete").all()
            effort = sum(p.effort or 0 for p in done_pbis)
            result.append({
                "sprint_id": sprint.id,
                "sprint_label": f"Sprint #{sprint.id}",
                "effort_completed": effort
            })
        return result