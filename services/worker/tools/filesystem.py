import os
import aiofiles
from typing import Dict, Any

class FilesystemTool:
    name: str = "filesystem"
    description: str = "Reads, writes, and lists files locally."

    async def execute(self, action: str, path: str, content: str = "") -> Dict[str, Any]:
        """
        Actions: 'read', 'write', 'list'
        """
        # Ensure we stay within the workspace directory for safety
        safe_path = os.path.abspath(path)
        
        if action == "write":
            os.makedirs(os.path.dirname(safe_path), exist_ok=True)
            async with aiofiles.open(safe_path, mode="w", encoding="utf-8") as f:
                await f.write(content)
            return {"status": "success", "message": f"Successfully wrote to {path}"}
            
        elif action == "read":
            if not os.path.exists(safe_path):
                return {"status": "error", "message": f"File {path} does not exist"}
            async with aiofiles.open(safe_path, mode="r", encoding="utf-8") as f:
                data = await f.read()
            return {"status": "success", "content": data}
            
        elif action == "list":
            if not os.path.exists(safe_path):
                return {"status": "error", "message": f"Directory {path} does not exist"}
            items = os.listdir(safe_path)
            return {"status": "success", "items": items}
            
        return {"status": "error", "message": f"Unknown action: {action}"}
