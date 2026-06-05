from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import mysql.connector
import hashlib
import os

app = FastAPI(title="SRMS - Osborn Matthew A I")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET","POST","PUT","DELETE","OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST","mysql-34014e96-osbornmatthew.l.aivencloud.com"),
        port=int(os.environ.get("DB_PORT","22276")),
        user=os.environ.get("DB_USER","avnadmin"),
        password=os.environ.get("DB_PASSWORD","AVNS_7mQ80zqZuSLI5Sx0JPR"),
        database=os.environ.get("DB_NAME","defaultdb"),
        ssl_disabled=os.environ.get("DB_SSL","tfalse").lower()=="false"
    )

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

class AdminLogin(BaseModel):
    username: str
    password: str

class StudentLogin(BaseModel):
    reg_no: str
    password: str

class StudentCreate(BaseModel):
    name: str
    reg_no: str
    department: str
    year: int
    email: Optional[str] = ""

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None
    email: Optional[str] = None

class ResultCreate(BaseModel):
    student_id: int
    subject_code: str
    subject_name: str
    grade: str
    credits: float
    semester: int

class PasswordChange(BaseModel):
    reg_no: str
    old_password: str
    new_password: str

@app.get("/health")
def health(): return {"status":"ok","dev":"Osborn Matthew A I"}

@app.post("/login/admin")
def admin_login(data: AdminLogin):
    db=get_db(); cur=db.cursor(dictionary=True)
    cur.execute("SELECT * FROM admins WHERE username=%s AND password=%s",(data.username,hash_pw(data.password)))
    a=cur.fetchone(); db.close()
    if not a: raise HTTPException(401,"Invalid credentials")
    return {"message":"ok","role":"admin"}

@app.post("/login/student")
def student_login(data: StudentLogin):
    db=get_db(); cur=db.cursor(dictionary=True)
    cur.execute("SELECT * FROM students WHERE reg_no=%s AND password=%s",(data.reg_no,hash_pw(data.password)))
    s=cur.fetchone(); db.close()
    if not s: raise HTTPException(401,"Invalid register number or password")
    return {"message":"ok","role":"student","student_id":s["id"],"name":s["name"],"reg_no":s["reg_no"],"department":s["department"],"year":s["year"],"email":s.get("email","")}

@app.post("/change-password")
def change_password(data: PasswordChange):
    db=get_db(); cur=db.cursor(dictionary=True)
    cur.execute("SELECT * FROM students WHERE reg_no=%s AND password=%s",(data.reg_no,hash_pw(data.old_password)))
    s=cur.fetchone()
    if not s: db.close(); raise HTTPException(401,"Wrong current password")
    cur.execute("UPDATE students SET password=%s WHERE reg_no=%s",(hash_pw(data.new_password),data.reg_no))
    db.commit(); db.close()
    return {"message":"Password changed"}

@app.get("/students")
def get_students():
    db=get_db(); cur=db.cursor(dictionary=True)
    cur.execute("SELECT id,name,reg_no,department,year,email,created_at FROM students ORDER BY name")
    rows=cur.fetchall(); db.close(); return rows

@app.post("/students")
def create_student(data: StudentCreate):
    db=get_db(); cur=db.cursor()
    try:
        cur.execute("INSERT INTO students (name,reg_no,department,year,email,password) VALUES (%s,%s,%s,%s,%s,%s)",
            (data.name,data.reg_no,data.department,data.year,data.email,hash_pw(data.reg_no)))
        db.commit(); sid=cur.lastrowid
    except Exception as e: db.close(); raise HTTPException(400,str(e))
    db.close(); return {"message":"Student added","id":sid}

@app.put("/students/{sid}")
def update_student(sid:int, data:StudentUpdate):
    db=get_db(); cur=db.cursor()
    fields={k:v for k,v in data.dict().items() if v is not None}
    if not fields: raise HTTPException(400,"No fields")
    sets=", ".join(f"{k}=%s" for k in fields)
    cur.execute(f"UPDATE students SET {sets} WHERE id=%s",(*fields.values(),sid))
    db.commit(); db.close(); return {"message":"Updated"}

@app.delete("/students/{sid}")
def delete_student(sid:int):
    db=get_db(); cur=db.cursor()
    cur.execute("DELETE FROM results WHERE student_id=%s",(sid,))
    cur.execute("DELETE FROM students WHERE id=%s",(sid,))
    db.commit(); db.close(); return {"message":"Deleted"}

@app.get("/results/{sid}")
def get_results(sid:int):
    db=get_db(); cur=db.cursor(dictionary=True)
    cur.execute("""SELECT r.*,s.name,s.reg_no,s.department,s.year
        FROM results r JOIN students s ON r.student_id=s.id
        WHERE r.student_id=%s ORDER BY r.semester,r.subject_code""",(sid,))
    rows=cur.fetchall(); db.close(); return rows

@app.post("/results")
def add_result(data:ResultCreate):
    if data.grade not in ['O','A+','A','B+','B','C','F']:
        raise HTTPException(400,"Invalid grade")
    db=get_db(); cur=db.cursor()
    cur.execute("INSERT INTO results (student_id,subject_code,subject_name,grade,credits,semester) VALUES (%s,%s,%s,%s,%s,%s)",
        (data.student_id,data.subject_code,data.subject_name,data.grade,data.credits,data.semester))
    db.commit(); db.close(); return {"message":"Result added"}

@app.delete("/results/{rid}")
def delete_result(rid:int):
    db=get_db(); cur=db.cursor()
    cur.execute("DELETE FROM results WHERE id=%s",(rid,))
    db.commit(); db.close(); return {"message":"Deleted"}

@app.get("/dashboard")
def dashboard():
    db=get_db(); cur=db.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) as total FROM students"); ts=cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) as total FROM results"); tr=cur.fetchone()["total"]
    cur.execute("SELECT department,COUNT(*) as count FROM students GROUP BY department"); dept=cur.fetchall()
    db.close(); return {"total_students":ts,"total_results":tr,"by_department":dept}

@app.get("/search")
def search(q:str):
    db=get_db(); cur=db.cursor(dictionary=True)
    like=f"%{q}%"
    cur.execute("SELECT id,name,reg_no,department,year,email FROM students WHERE name LIKE %s OR reg_no LIKE %s",(like,like))
    rows=cur.fetchall(); db.close(); return rows
