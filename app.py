# import json
# import os
# import logging
# import uuid
# from io import BytesIO
# from pathlib import Path
# from urllib.parse import urlencode
# from PIL import Image, UnidentifiedImageError
# from fastapi import BackgroundTasks

# import qrcode
# from dotenv import load_dotenv
# from fastapi.responses import FileResponse, StreamingResponse
# from fastapi.staticfiles import StaticFiles


# BASE_DIR = Path(__file__).resolve().parent
# load_dotenv(BASE_DIR / ".env", override=False)

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("ecopulse")

# from fastapi import (
#     FastAPI,
#     HTTPException,
#     Query,
#     UploadFile,
#     File,
#     Form,
# )
# from database import get_connection, init_db
# from models import (
#     IssueCreate,
#     StatusUpdate,
#     RepairVerificationCreate,
#     LocationCreate,
#     WaterSimulation,
#     ElectricitySimulation,
#     PlasticSimulation,
#     StaffAssignment,
# )
# from prioritization import prioritize_issue
# from simulator import (
#     simulate_water,
#     simulate_electricity,
#     simulate_plastic,
# )

# try:
#     from ai_engine import analyze_issue
# except ImportError:
#     logger.exception("Could not import ai_engine.py")
#     analyze_issue = None


# STATIC_DIR = BASE_DIR / "static"
# APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")
# DEFAULT_CATEGORY = "Other Sustainability Issue"

# app = FastAPI(
#     title="EcoPulse AI",
#     description=(
#         "Campus sustainability issue reporting, AI-assisted priority "
#         "assessment, repair verification, impact simulation, and analytics."
#     ),
#     version="1.2.0",
# )

# STATIC_DIR.mkdir(parents=True, exist_ok=True)
# app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# UPLOAD_DIR = BASE_DIR / "uploads"
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ALLOWED_PHOTO_TYPES = {
#     "image/jpeg": ".jpg",
#     "image/png": ".png",
#     "image/webp": ".webp",
# }

# MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB


# async def save_issue_photo(photo: UploadFile | None) -> str:
#     """Validate and save an optional issue photo."""

#     if photo is None or not photo.filename:
#         return ""

#     extension = ALLOWED_PHOTO_TYPES.get(photo.content_type)

#     if not extension:
#         await photo.close()
#         raise HTTPException(
#             status_code=400,
#             detail="Only JPEG, PNG, and WebP photos are allowed.",
#         )

#     filename = f"{uuid.uuid4().hex}{extension}"
#     destination = UPLOAD_DIR / filename
#     size = 0

#     try:
#         # Read the upload with a strict size limit.
#         with destination.open("wb") as output:
#             while True:
#                 chunk = await photo.read(64 * 1024)

#                 if not chunk:
#                     break

#                 size += len(chunk)

#                 if size > MAX_PHOTO_SIZE:
#                     raise HTTPException(
#                         status_code=413,
#                         detail="Photo must be 5 MB or smaller.",
#                     )

#                 output.write(chunk)

#         if size == 0:
#             raise HTTPException(
#                 status_code=400,
#                 detail="The uploaded photo is empty.",
#             )

#         # Verify that the file contains a recognizable image.
#         try:
#             with Image.open(destination) as image:
#                 image.verify()

#             with Image.open(destination) as image:
#                 if image.format not in {"JPEG", "PNG", "WEBP"}:
#                     raise HTTPException(
#                         status_code=400,
#                         detail="Unsupported image format.",
#                     )
#         except (UnidentifiedImageError, OSError):
#             raise HTTPException(
#                 status_code=400,
#                 detail="The uploaded file is not a valid image.",
#             )

#         return f"/uploads/{filename}"

#     except Exception:
#         destination.unlink(missing_ok=True)
#         raise

#     finally:
#         await photo.close()

# # ---------------------------------------------------------
# # STARTUP AND FRONTEND
# # ---------------------------------------------------------

# @app.on_event("startup")
# def startup():
#     init_db()
#     logger.info("EcoPulse AI database initialized.")
#     logger.info("Gemini engine imported: %s", analyze_issue is not None)
#     logger.info(
#         "Gemini API key configured: %s",
#         bool(os.getenv("GEMINI_API_KEY")),
#     )
#     logger.info(
#         "Configured Gemini model: %s",
#         os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
#     )


# @app.get("/", include_in_schema=False)
# def home():
#     index_file = STATIC_DIR / "index.html"

#     if not index_file.exists():
#         raise HTTPException(
#             status_code=404,
#             detail="Frontend not created yet. Create static/index.html first.",
#         )

#     return FileResponse(index_file)


# # ---------------------------------------------------------
# # DATABASE HELPERS
# # ---------------------------------------------------------

# def row_to_dict(row):
#     if row is None:
#         return None

#     result = dict(row)

#     if "priority_reasons" in result:
#         try:
#             result["priority_reasons"] = json.loads(
#                 result["priority_reasons"] or "[]"
#             )
#         except (TypeError, json.JSONDecodeError):
#             result["priority_reasons"] = []

#     if "ai_missing_information" in result:
#         try:
#             result["ai_missing_information"] = json.loads(
#                 result["ai_missing_information"] or "[]"
#             )
#         except (TypeError, json.JSONDecodeError):
#             result["ai_missing_information"] = []

#     if "near_electrical" in result:
#         result["near_electrical"] = bool(result["near_electrical"])

#     if "confirmed" in result:
#         result["confirmed"] = bool(result["confirmed"])

#     if "ai_analyzed" in result:
#         result["ai_analyzed"] = bool(result["ai_analyzed"])

#     return result


# def get_issue_or_404(connection, issue_id):
#     row = connection.execute(
#         "SELECT * FROM issues WHERE id = ?",
#         (issue_id,),
#     ).fetchone()

#     if row is None:
#         raise HTTPException(status_code=404, detail="Issue not found.")

#     return row


# # def record_status_change(
# #     connection,
# #     issue_id,
# #     previous_status,
# #     new_status,
# #     notes="",
# # ):
# #     connection.execute(
# #         """
# #         INSERT INTO issue_history
# #         (issue_id, previous_status, new_status, notes)
# #         VALUES (?, ?, ?, ?)
# #         """,
# #         (issue_id, previous_status, new_status, notes),
# #     )

# #     connection.execute(
# #         """
# #         UPDATE issues
# #         SET status = ?, updated_at = CURRENT_TIMESTAMP
# #         WHERE id = ?
# #         """,
# #         (new_status, issue_id),
# #     )


# def record_status_change(
#     connection,
#     issue_id,
#     previous_status,
#     new_status,
#     notes="",
# ):
#     # Save the status change in the history table.
#     connection.execute(
#         """
#         INSERT INTO issue_history
#         (issue_id, previous_status, new_status, notes)
#         VALUES (?, ?, ?, ?)
#         """,
#         (issue_id, previous_status, new_status, notes),
#     )

#     # Update status and record the relevant timestamps.
#     if new_status == "In Progress":
#         connection.execute(
#             """
#             UPDATE issues
#             SET status = ?,
#                 updated_at = CURRENT_TIMESTAMP,
#                 in_progress_at = COALESCE(
#                     in_progress_at, CURRENT_TIMESTAMP
#                 ),
#                 resolved_at = NULL
#             WHERE id = ?
#             """,
#             (new_status, issue_id),
#         )

#     elif new_status == "Resolved":
#         connection.execute(
#             """
#             UPDATE issues
#             SET status = ?,
#                 updated_at = CURRENT_TIMESTAMP,
#                 resolved_at = CURRENT_TIMESTAMP
#             WHERE id = ?
#             """,
#             (new_status, issue_id),
#         )

#     elif new_status == "Reopened":
#         connection.execute(
#             """
#             UPDATE issues
#             SET status = ?,
#                 updated_at = CURRENT_TIMESTAMP,
#                 resolved_at = NULL
#             WHERE id = ?
#             """,
#             (new_status, issue_id),
#         )

#     else:
#         connection.execute(
#             """
#             UPDATE issues
#             SET status = ?, updated_at = CURRENT_TIMESTAMP
#             WHERE id = ?
#             """,
#             (new_status, issue_id),
#         )

# # ---------------------------------------------------------
# # HEALTH CHECK
# # ---------------------------------------------------------

# @app.get("/api/health")
# def health():
#     with get_connection() as connection:
#         connection.execute("SELECT 1").fetchone()

#     return {
#         "status": "healthy",
#         "application": "EcoPulse AI",
#         "database": "connected",
#         "ai_available": (
#             analyze_issue is not None
#             and bool(os.getenv("GEMINI_API_KEY"))
#         ),
#         "ai_model": os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
#     }


# # ---------------------------------------------------------
# # MODULE 1: AI-ASSISTED ISSUE PRIORITY ENGINE
# # ---------------------------------------------------------
# @app.post("/api/issues", status_code=201)
# async def create_issue(
#     issue: str = Form(...),
#     photo: UploadFile | None = File(default=None),
# ):
#     """
#     Gemini provides advisory analysis when available.
#     Rule-based prioritization determines the official priority and action.
#     Reports can still be saved when Gemini is unavailable.
#     """

#     # Convert the submitted JSON string into a validated issue model.
#     try:
#         issue = IssueCreate.model_validate_json(issue)
#     except Exception:
#         raise HTTPException(
#             status_code=422,
#             detail="Invalid issue form data.",
#         )

#     # Save the optional photo.
#     photo_path = await save_issue_photo(photo)

#     ai_result = {
#         "urgency": "Unknown",
#         "explanation": (
#             "AI analysis was unavailable. Priority was calculated "
#             "using the report values and rule-based assessment."
#         ),
#         "missing_information": [],
#         "recommended_action": "",
#     }

#     ai_analyzed = False
#     ai_error = ""

#     category = issue.category or DEFAULT_CATEGORY
#     severity = issue.severity
#     safety_risk = issue.safety_risk
#     near_electrical = issue.near_electrical
#     resource_loss = issue.estimated_resource_loss

#     api_key_present = bool(os.getenv("GEMINI_API_KEY"))

#     if analyze_issue is None:
#         ai_error = "The ai_engine module could not be imported."
#         logger.error("[Gemini] %s", ai_error)

#     elif not api_key_present:
#         ai_error = (
#             "GEMINI_API_KEY is missing from the environment. "
#             "Check the .env file in the project directory."
#         )
#         logger.error("[Gemini] %s", ai_error)

#     else:
#         try:
#             logger.info(
#                 "[Gemini] Analyzing new issue: %s",
#                 issue.title,
#             )

#             candidate = analyze_issue(
#                 description=issue.description,
#                 building=issue.building,
#                 location=issue.location_details,
#             )

#             if not isinstance(candidate, dict):
#                 raise ValueError(
#                     "Gemini returned an invalid response; "
#                     "expected a dictionary."
#                 )

#             required_fields = (
#                 "category",
#                 "severity",
#                 "safety_risk",
#                 "near_electrical",
#                 "estimated_resource_loss",
#                 "urgency",
#                 "explanation",
#                 "missing_information",
#                 "recommended_action",
#             )

#             missing_fields = [
#                 field
#                 for field in required_fields
#                 if field not in candidate
#             ]

#             if missing_fields:
#                 raise ValueError(
#                     "Gemini response is missing fields: "
#                     + ", ".join(missing_fields)
#                 )

#             allowed_categories = {
#                 "Water Leakage",
#                 "Overflowing Tank",
#                 "Electricity Wastage",
#                 "Lighting or Fan Left On",
#                 "Waste Management",
#                 "Single-Use Plastic",
#                 "Other Sustainability Issue",
#             }

#             if candidate["category"] not in allowed_categories:
#                 raise ValueError(
#                     "Gemini returned an unsupported category."
#                 )

#             for field in ("severity", "safety_risk"):
#                 value = candidate[field]

#                 if (
#                     isinstance(value, bool)
#                     or not isinstance(value, int)
#                     or not 1 <= value <= 5
#                 ):
#                     raise ValueError(
#                         f"Gemini returned an invalid {field}."
#                     )

#             if not isinstance(candidate["near_electrical"], bool):
#                 raise ValueError(
#                     "Gemini returned an invalid near_electrical value."
#                 )

#             if candidate["urgency"] not in {
#                 "Low", "Medium", "High", "Critical"
#             }:
#                 raise ValueError(
#                     "Gemini returned an invalid urgency."
#                 )

#             if not isinstance(candidate["explanation"], str):
#                 raise ValueError(
#                     "Gemini returned an invalid explanation."
#                 )

#             if not isinstance(candidate["recommended_action"], str):
#                 raise ValueError(
#                     "Gemini returned an invalid recommended action."
#                 )

#             if not isinstance(candidate["missing_information"], list):
#                 raise ValueError(
#                     "Gemini returned an invalid missing_information list."
#                 )

#             candidate_loss = candidate["estimated_resource_loss"]

#             if (
#                 isinstance(candidate_loss, bool)
#                 or not isinstance(candidate_loss, (int, float))
#                 or not 0 <= candidate_loss <= 1_000_000
#             ):
#                 raise ValueError(
#                     "Gemini returned an invalid estimated resource loss."
#                 )

#             if issue.category is None:
#                 category = candidate["category"]

#             severity = candidate["severity"]
#             safety_risk = candidate["safety_risk"]
#             near_electrical = candidate["near_electrical"]
#             resource_loss = float(candidate_loss)

#             ai_result = candidate
#             ai_analyzed = True

#             logger.info(
#                 "[Gemini] Analysis succeeded for issue: %s",
#                 issue.title,
#             )

#         except Exception as error:
#             ai_error = f"{type(error).__name__}: {error}"

#             logger.exception(
#                 "[Gemini AI ERROR] Analysis failed for issue '%s'",
#                 issue.title,
#             )

#             ai_result = {
#                 "urgency": "Unknown",
#                 "explanation": (
#                     "AI analysis was unavailable. Priority was calculated "
#                     "using the report values and rule-based assessment."
#                 ),
#                 "missing_information": [],
#                 "recommended_action": "",
#             }

#     # Official priority remains rule-based.
#     assessment = prioritize_issue(
#         category=category,
#         severity=severity,
#         safety_risk=safety_risk,
#         resource_loss=resource_loss,
#         unresolved_hours=issue.unresolved_hours,
#         near_electrical=near_electrical,
#     )

#     ai_explanation = ai_result.get(
#         "explanation",
#         "No AI explanation is available.",
#     )

#     if not isinstance(ai_explanation, str):
#         ai_explanation = "No AI explanation is available."

#     ai_missing_information = ai_result.get(
#         "missing_information", []
#     )

#     if not isinstance(ai_missing_information, list):
#         ai_missing_information = []

#     ai_missing_information = [
#         str(item) for item in ai_missing_information[:10]
#     ]

#     # Keep official and AI recommendations separate.
#     official_action = assessment["recommended_action"]
#     ai_recommended_action = ai_result.get(
#         "recommended_action", ""
#     )

#     if not isinstance(ai_recommended_action, str):
#         ai_recommended_action = ""

#     with get_connection() as connection:
#         cursor = connection.execute(
#             """
#             INSERT INTO issues (
#                 title,
#                 category,
#                 building,
#                 location_details,
#                 description,
#                 severity,
#                 safety_risk,
#                 near_electrical,
#                 estimated_resource_loss,
#                 unresolved_hours,
#                 priority_score,
#                 priority_level,
#                 priority_reasons,
#                 recommended_action,
#                 status,
#                 reporter_name,
#                 reporter_contact,
#                 photo_path,
#                 ai_urgency,
#                 ai_explanation,
#                 ai_recommended_action,
#                 ai_missing_information,
#                 ai_analyzed
#             )
#             VALUES (
#                 ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
#                 ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
#             )
#             """,
#             (
#                 issue.title,
#                 category,
#                 issue.building,
#                 issue.location_details,
#                 issue.description,
#                 severity,
#                 safety_risk,
#                 int(near_electrical),
#                 resource_loss,
#                 issue.unresolved_hours,
#                 assessment["priority_score"],
#                 assessment["priority_level"],
#                 json.dumps(assessment["priority_reasons"]),
#                 official_action,
#                 "Reported",
#                 issue.reporter_name,
#                 issue.reporter_contact,
#                 photo_path,
#                 ai_result.get("urgency", "Unknown"),
#                 ai_explanation,
#                 ai_recommended_action,
#                 json.dumps(ai_missing_information),
#                 int(ai_analyzed),
#             ),
#         )

#         issue_id = cursor.lastrowid

#         connection.execute(
#             """
#             INSERT INTO issue_history (
#                 issue_id,
#                 previous_status,
#                 new_status,
#                 notes
#             )
#             VALUES (?, NULL, 'Reported', 'Issue created')
#             """,
#             (issue_id,),
#         )

#         saved_issue = connection.execute(
#             "SELECT * FROM issues WHERE id = ?",
#             (issue_id,),
#         ).fetchone()

#     logger.info(
#         "[Issue] Saved issue ID %s; Gemini analyzed: %s",
#         issue_id,
#         ai_analyzed,
#     )

#     return {
#         "message": "Sustainability issue reported successfully.",
#         "issue": row_to_dict(saved_issue),
#         "ai": {
#             "analyzed": ai_analyzed,
#             "urgency": ai_result.get("urgency", "Unknown"),
#             "explanation": ai_explanation,
#             "missing_information": ai_missing_information,
#             "suggested_action": ai_recommended_action,
#             "error": ai_error if not ai_analyzed else "",
#         },
#     }

# @app.get("/api/issues")
# def list_issues(
#     status: str | None = None,
#     priority: str | None = None,
#     category: str | None = None,
#     building: str | None = None,
#     q: str | None = Query(default=None, max_length=200),
#     limit: int = Query(default=100, ge=1, le=500),
#     offset: int = Query(default=0, ge=0),
# ):
#     conditions = []
#     parameters = []

#     if status:
#         conditions.append("status = ?")
#         parameters.append(status)

#     if priority:
#         conditions.append("priority_level = ?")
#         parameters.append(priority)

#     if category:
#         conditions.append("category = ?")
#         parameters.append(category)

#     if building:
#         conditions.append("building LIKE ?")
#         parameters.append(f"%{building}%")

#     if q:
#         conditions.append(
#             "(title LIKE ? OR description LIKE ? OR location_details LIKE ?)"
#         )
#         search_term = f"%{q}%"
#         parameters.extend([search_term, search_term, search_term])

#     where_clause = (
#         "WHERE " + " AND ".join(conditions)
#         if conditions
#         else ""
#     )

#     with get_connection() as connection:
#         total = connection.execute(
#             f"SELECT COUNT(*) FROM issues {where_clause}",
#             parameters,
#         ).fetchone()[0]

#         rows = connection.execute(
#             f"""
#             SELECT * FROM issues
#             {where_clause}
#             ORDER BY
#                 CASE priority_level
#                     WHEN 'Critical' THEN 0
#                     WHEN 'High' THEN 1
#                     WHEN 'Medium' THEN 2
#                     ELSE 3
#                 END,
#                 created_at DESC
#             LIMIT ? OFFSET ?
#             """,
#             parameters + [limit, offset],
#         ).fetchall()

#     return {
#         "total": total,
#         "limit": limit,
#         "offset": offset,
#         "issues": [row_to_dict(row) for row in rows],
#     }


# @app.get("/api/issues/{issue_id}")
# def get_issue(issue_id: int):
#     with get_connection() as connection:
#         issue = get_issue_or_404(connection, issue_id)

#         history = connection.execute(
#             """
#             SELECT * FROM issue_history
#             WHERE issue_id = ?
#             ORDER BY changed_at DESC, id DESC
#             """,
#             (issue_id,),
#         ).fetchall()

#         repairs = connection.execute(
#             """
#             SELECT * FROM repair_verifications
#             WHERE issue_id = ?
#             ORDER BY completed_at DESC, id DESC
#             """,
#             (issue_id,),
#         ).fetchall()

#     return {
#         "issue": row_to_dict(issue),
#         "history": [row_to_dict(row) for row in history],
#         "repairs": [row_to_dict(row) for row in repairs],
#     }


# @app.patch("/api/issues/{issue_id}/status")
# def update_issue_status(issue_id: int, update: StatusUpdate):
#     requested_status = update.status

#     with get_connection() as connection:
#         issue = get_issue_or_404(connection, issue_id)
#         current_status = issue["status"]

#         allowed_transitions = {
#             "Reported": {"Acknowledged"},
#             "Acknowledged": {"In Progress"},
#             "In Progress": set(),
#             "Resolved": {"Reopened"},
#             "Reopened": {"Acknowledged", "In Progress"},
#         }

#         if requested_status == current_status:
#             raise HTTPException(
#                 status_code=400,
#                 detail="The issue already has this status.",
#             )

#         if requested_status not in allowed_transitions.get(
#             current_status, set()
#         ):
#             raise HTTPException(
#                 status_code=400,
#                 detail=(
#                     f"Cannot change status from {current_status} "
#                     f"to {requested_status}. Follow the repair workflow."
#                 ),
#             )

#         if requested_status == "Reopened":
#             connection.execute(
#                 """
#                 UPDATE repair_verifications
#                 SET confirmed = 0, reopened_at = CURRENT_TIMESTAMP
#                 WHERE issue_id = ? AND confirmed = 1
#                 """,
#                 (issue_id,),
#             )

#         record_status_change(
#             connection,
#             issue_id,
#             current_status,
#             requested_status,
#             update.notes,
#         )

#         updated = connection.execute(
#             "SELECT * FROM issues WHERE id = ?",
#             (issue_id,),
#         ).fetchone()

#     return {
#         "message": "Issue status updated.",
#         "issue": row_to_dict(updated),
#     }


# # ---------------------------------------------------------
# # MODULE 3: REPAIR VERIFICATION AND REOPENING
# # ---------------------------------------------------------

# @app.post("/api/issues/{issue_id}/repair-verification", status_code=201)
# def verify_repair(
#     issue_id: int,
#     verification: RepairVerificationCreate,
# ):
#     with get_connection() as connection:
#         issue = get_issue_or_404(connection, issue_id)
#         current_status = issue["status"]

#         if current_status != "In Progress":
#             raise HTTPException(
#                 status_code=400,
#                 detail=(
#                     "An issue must be In Progress before repair "
#                     "verification can be submitted."
#                 ),
#             )

#         cursor = connection.execute(
#             """
#             INSERT INTO repair_verifications (
#                 issue_id,
#                 repair_action,
#                 completion_notes,
#                 estimated_repair_cost,
#                 confirmed
#             )
#             VALUES (?, ?, ?, ?, ?)
#             """,
#             (
#                 issue_id,
#                 verification.repair_action,
#                 verification.completion_notes,
#                 verification.estimated_repair_cost,
#                 int(verification.confirmed),
#             ),
#         )

#         repair_id = cursor.lastrowid

#         if verification.confirmed:
#             record_status_change(
#                 connection,
#                 issue_id,
#                 current_status,
#                 "Resolved",
#                 (
#                     "Repair confirmation submitted. "
#                     + verification.completion_notes
#                 ),
#             )

#         repair = connection.execute(
#             "SELECT * FROM repair_verifications WHERE id = ?",
#             (repair_id,),
#         ).fetchone()

#         updated_issue = connection.execute(
#             "SELECT * FROM issues WHERE id = ?",
#             (issue_id,),
#         ).fetchone()

#     return {
#         "message": (
#             "Repair confirmed and issue resolved."
#             if verification.confirmed
#             else "Repair record saved; issue remains In Progress."
#         ),
#         "repair": row_to_dict(repair),
#         "issue": row_to_dict(updated_issue),
#     }


# # ---------------------------------------------------------
# # CAMPUS LOCATIONS AND QR REPORTING
# # ---------------------------------------------------------

# @app.post("/api/locations", status_code=201)
# def create_location(location: LocationCreate):
#     try:
#         with get_connection() as connection:
#             cursor = connection.execute(
#                 """
#                 INSERT INTO campus_locations (
#                     building_name,
#                     location_name,
#                     location_details
#                 )
#                 VALUES (?, ?, ?)
#                 """,
#                 (
#                     location.building_name.strip(),
#                     location.location_name.strip(),
#                     location.location_details.strip(),
#                 ),
#             )

#             saved = connection.execute(
#                 "SELECT * FROM campus_locations WHERE id = ?",
#                 (cursor.lastrowid,),
#             ).fetchone()

#     except Exception as error:
#         if "UNIQUE constraint failed" in str(error):
#             raise HTTPException(
#                 status_code=409,
#                 detail="This location already exists in this building.",
#             ) from error
#         raise

#     return {
#         "message": "Campus location created.",
#         "location": row_to_dict(saved),
#     }


# @app.get("/api/locations")
# def list_locations():
#     with get_connection() as connection:
#         rows = connection.execute(
#             """
#             SELECT * FROM campus_locations
#             ORDER BY building_name, location_name
#             """
#         ).fetchall()

#     return {"locations": [row_to_dict(row) for row in rows]}


# @app.get("/api/locations/{location_id}/qr")
# def generate_location_qr(location_id: int):
#     with get_connection() as connection:
#         location = connection.execute(
#             "SELECT * FROM campus_locations WHERE id = ?",
#             (location_id,),
#         ).fetchone()

#     if location is None:
#         raise HTTPException(status_code=404, detail="Location not found.")

#     report_url = (
#         APP_BASE_URL.rstrip("/")
#         + "/?"
#         + urlencode({
#             "building": location["building_name"],
#             "location": location["location_name"],
#         })
#     )

#     qr = qrcode.QRCode(
#         version=None,
#         error_correction=qrcode.constants.ERROR_CORRECT_M,
#         box_size=8,
#         border=4,
#     )
#     qr.add_data(report_url)
#     qr.make(fit=True)

#     image = qr.make_image(fill_color="black", back_color="white")
#     image_bytes = BytesIO()
#     image.save(image_bytes, format="PNG")
#     image_bytes.seek(0)

#     return StreamingResponse(
#         image_bytes,
#         media_type="image/png",
#         headers={
#             "Content-Disposition": (
#                 f'inline; filename="ecopulse-location-{location_id}.png"'
#             )
#         },
#     )


# # ---------------------------------------------------------
# # MODULE 2: CAMPUS WHAT-IF IMPACT SIMULATOR
# # ---------------------------------------------------------

# @app.post("/api/simulate/water")
# def water_impact_simulation(inputs: WaterSimulation):
#     try:
#         return simulate_water(
#             leakage_litres_per_hour=inputs.leakage_litres_per_hour,
#             hours_avoided=inputs.hours_avoided,
#         )
#     except ValueError as error:
#         raise HTTPException(status_code=422, detail=str(error)) from error


# @app.post("/api/simulate/electricity")
# def electricity_impact_simulation(inputs: ElectricitySimulation):
#     try:
#         return simulate_electricity(
#             power_kw_per_device=inputs.power_kw_per_device,
#             device_count=inputs.device_count,
#             hours_avoided=inputs.hours_avoided,
#             tariff_per_kwh=inputs.tariff_per_kwh,
#             emission_factor=inputs.emission_factor,
#         )
#     except ValueError as error:
#         raise HTTPException(status_code=422, detail=str(error)) from error


# @app.post("/api/simulate/plastic")
# def plastic_impact_simulation(inputs: PlasticSimulation):
#     try:
#         return simulate_plastic(inputs.items_avoided)
#     except ValueError as error:
#         raise HTTPException(status_code=422, detail=str(error)) from error


# # ---------------------------------------------------------
# # MODULE 4: SUSTAINABILITY IMPACT DASHBOARD
# # ---------------------------------------------------------

# @app.get("/api/dashboard/summary")
# def dashboard_summary():
#     with get_connection() as connection:
#         total = connection.execute(
#             "SELECT COUNT(*) FROM issues"
#         ).fetchone()[0]

#         open_count = connection.execute(
#             """
#             SELECT COUNT(*) FROM issues
#             WHERE status != 'Resolved'
#             """
#         ).fetchone()[0]

#         resolved = connection.execute(
#             """
#             SELECT COUNT(*) FROM issues
#             WHERE status = 'Resolved'
#             """
#         ).fetchone()[0]

#         high_priority = connection.execute(
#             """
#             SELECT COUNT(*) FROM issues
#             WHERE priority_level IN ('Critical', 'High')
#               AND status != 'Resolved'
#             """
#         ).fetchone()[0]

#         by_status_rows = connection.execute(
#             """
#             SELECT status, COUNT(*) AS count
#             FROM issues
#             GROUP BY status
#             ORDER BY status
#             """
#         ).fetchall()

#         by_priority_rows = connection.execute(
#             """
#             SELECT priority_level, COUNT(*) AS count
#             FROM issues
#             GROUP BY priority_level
#             ORDER BY
#                 CASE priority_level
#                     WHEN 'Critical' THEN 0
#                     WHEN 'High' THEN 1
#                     WHEN 'Medium' THEN 2
#                     ELSE 3
#                 END
#             """
#         ).fetchall()

#         by_category_rows = connection.execute(
#             """
#             SELECT category, COUNT(*) AS count
#             FROM issues
#             GROUP BY category
#             ORDER BY count DESC, category
#             """
#         ).fetchall()

#         daily_rows = connection.execute(
#             """
#             SELECT DATE(created_at) AS date, COUNT(*) AS count
#             FROM issues
#             WHERE created_at >= DATE('now', '-6 days')
#             GROUP BY DATE(created_at)
#             ORDER BY date
#             """
#         ).fetchall()

#         repair_count = connection.execute(
#             """
#             SELECT COUNT(*) FROM repair_verifications
#             WHERE confirmed = 1
#             """
#         ).fetchone()[0]

#         ai_analyzed_count = connection.execute(
#             """
#             SELECT COUNT(*) FROM issues
#             WHERE ai_analyzed = 1
#             """
#         ).fetchone()[0]

#     return {
#         "total_issues": total,
#         "open_issues": open_count,
#         "resolved_issues": resolved,
#         "high_priority_open_issues": high_priority,
#         "confirmed_repairs": repair_count,
#         "ai_analyzed_issues": ai_analyzed_count,
#         "by_status": [dict(row) for row in by_status_rows],
#         "by_priority": [dict(row) for row in by_priority_rows],
#         "by_category": [dict(row) for row in by_category_rows],
#         "daily_reports": [dict(row) for row in daily_rows],
#         "note": (
#             "Environmental savings are estimates and should be "
#             "calculated from verified repair data and stated assumptions."
#         ),
#     }


# @app.get("/api/dashboard/recent-issues")
# def recent_issues(
#     limit: int = Query(default=5, ge=1, le=20),
# ):
#     with get_connection() as connection:
#         rows = connection.execute(
#             """
#             SELECT * FROM issues
#             ORDER BY created_at DESC, id DESC
#             LIMIT ?
#             """,
#             (limit,),
#         ).fetchall()

#     return {"issues": [row_to_dict(row) for row in rows]}


# @app.patch("/api/issues/{issue_id}/assign")
# def assign_staff(issue_id: int, assignment: StaffAssignment):
#     with get_connection() as connection:
#         issue = connection.execute(
#             "SELECT id, status FROM issues WHERE id = ?",
#             (issue_id,),
#         ).fetchone()

#         if issue is None:
#             raise HTTPException(status_code=404, detail="Issue not found")

#         connection.execute(
#             """
#             UPDATE issues
#             SET assigned_staff = ?,
#                 updated_at = CURRENT_TIMESTAMP
#             WHERE id = ?
#             """,
#             (assignment.assigned_staff.strip(), issue_id),
#         )

#         message = f"Issue #{issue_id} assigned to {assignment.assigned_staff.strip()}."

#         if assignment.notes.strip():
#             message += f" Notes: {assignment.notes.strip()}"

#         connection.execute(
#             """
#             INSERT INTO notifications (issue_id, recipient_name, message)
#             VALUES (?, ?, ?)
#             """,
#             (issue_id, assignment.assigned_staff.strip(), message),
#         )

#         return {
#             "message": "Staff assigned successfully",
#             "issue_id": issue_id,
#             "assigned_staff": assignment.assigned_staff.strip(),
#         }

# # ---------------------------------------------------------
# # RUN APPLICATION
# # ---------------------------------------------------------

# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(
#         "app:app",
#         host="127.0.0.1",
#         port=8000,
#         reload=True,
#     )



import json
import os
import logging
import uuid
from io import BytesIO
from pathlib import Path
from urllib.parse import urlencode
from PIL import Image, UnidentifiedImageError

import qrcode
from dotenv import load_dotenv
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=False)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ecopulse")

from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    Query,
    UploadFile,
    File,
    Form,
)
from database import get_connection, init_db
from models import (
    IssueCreate,
    StatusUpdate,
    RepairVerificationCreate,
    LocationCreate,
    WaterSimulation,
    ElectricitySimulation,
    PlasticSimulation,
    StaffAssignment,
)
from prioritization import prioritize_issue
from simulator import (
    simulate_water,
    simulate_electricity,
    simulate_plastic,
)

try:
    from ai_engine import analyze_issue
except ImportError:
    logger.exception("Could not import ai_engine.py")
    analyze_issue = None


STATIC_DIR = BASE_DIR / "static"
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_CATEGORY = "Other Sustainability Issue"

app = FastAPI(
    title="EcoPulse AI",
    description=(
        "Campus sustainability issue reporting, AI-assisted priority "
        "assessment, repair verification, impact simulation, and analytics."
    ),
    version="1.2.0",
)

STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_PHOTO_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB


async def save_issue_photo(photo: UploadFile | None) -> str:
    """Validate and save an optional issue photo."""

    if photo is None or not photo.filename:
        return ""

    extension = ALLOWED_PHOTO_TYPES.get(photo.content_type)

    if not extension:
        await photo.close()
        raise HTTPException(

