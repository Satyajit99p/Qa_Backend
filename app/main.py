from fastapi import FastAPI
from app.api import routes
import debugpy

debugpy.listen(("0.0.0.0", 5678))
print("Debugger waiting on port 5678…")

app = FastAPI(title="Document QA Backend")
app.include_router(routes.router)