import os
import sys
import json

def export_conversation(conv_id, output_dir):
    brain_dir = f"/home/sergio/.gemini/antigravity/brain/{conv_id}"
    if not os.path.exists(brain_dir):
        print(f"Error: No brain directory found for ID {conv_id}")
        return

    output_file = os.path.join(output_dir, f"{conv_id}_TechnicalRecord.md")
    
    with open(output_file, "w", encoding="utf-8") as out:
        out.write(f"# Registro de Conversación Técnico: {conv_id}\n\n")
        
        # 1. Implementation Plan
        plan_path = os.path.join(brain_dir, "implementation_plan.md")
        if os.path.exists(plan_path):
            out.write("## Plan de Implementación\n\n")
            with open(plan_path, "r") as f:
                out.write(f.read())
            out.write("\n\n---\n\n")
        
        # 2. Walkthrough
        walkthrough_path = os.path.join(brain_dir, "walkthrough.md")
        if os.path.exists(walkthrough_path):
            out.write("## Resumen de Resultados (Walkthrough)\n\n")
            with open(walkthrough_path, "r") as f:
                out.write(f.read())
            out.write("\n\n---\n\n")

    print(f"Exportado correctamente a: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 history_exporter.py <conv_id> <output_directory>")
        sys.exit(1)
        
    conv_id = sys.argv[1]
    output_dir = sys.argv[2]
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    export_conversation(conv_id, output_dir)
