import os

def create_project_map(start_path, output_file=None, exclude_files=None, exclude_dirs=None):
    exclude_files = exclude_files or []
    exclude_dirs = exclude_dirs or []

    def traverse_directory(path, indent=0):
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            return []
        
        project_map = []
        for entry in entries:
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                if entry not in exclude_dirs:
                    project_map.append(f"{'    ' * indent}📂 {entry}/")
                    project_map.extend(traverse_directory(full_path, indent + 1))
            elif entry not in exclude_files:
                project_map.append(f"{'    ' * indent}📄 {entry}")
        return project_map

    project_map = [f"Project Map: {start_path}\n"]
    project_map.extend(traverse_directory(start_path))

    project_map_str = "\n".join(project_map)
    print(project_map_str)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(project_map_str)
        print(f"\nProject map saved to: {output_file}")

# Usage example
if __name__ == "__main__":
    project_root = "."  # Current directory; change to your project's root if needed
    output_filename = "project_map.txt"  # Optional: save to a file

    excluded_files = ["README.md", "config.py", "assets", ".DS_Store"]
    excluded_dirs = ["__pycache__", "node_modules", ".venv", "assets"]

    create_project_map(project_root, output_file=output_filename, exclude_files=excluded_files, exclude_dirs=excluded_dirs)