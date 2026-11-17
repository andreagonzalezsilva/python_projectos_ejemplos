import json
import os
import urllib.request

# 1. Carga las variables del archivo .env (en la misma carpeta que este script)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

if os.path.exists(env_path):
  with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
      line = line.strip()
      if not line or line.startswith("#") or "=" not in line:
        continue
      key, value = line.split("=", 1)
      os.environ.setdefault(key.strip(), value.strip())

try:
  api_key = os.environ.get("OPENROUTER_API_KEY")
  if not api_key or not api_key.startswith("sk-or-v1-"):
    print(
        "❌ No se encontró una clave válida en OPENROUTER_API_KEY dentro de"
        " .env"
    )
    exit(1)

  # 2. Consulta el estado de la clave en OpenRouter
  req = urllib.request.Request(
      "https://openrouter.ai/api/v1/key",
      headers={"Authorization": f"Bearer {api_key}"},
  )

  with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())["data"]

  # 3. Muestra el resumen pedagógico
  label = data.get("label", "Estudiante")
  limit = data.get("limit")
  usage = data.get("usage", 0.0)
  limit_remaining = data.get("limit_remaining")

  print("\n" + "=" * 40)
  print(f"📊 ESTADO DE TU SALDO IA ({label})")
  print("=" * 40)
  print(f"• Consumo acumulado : ${usage:.3f} USD")

  if limit is not None:
    print(f"• Límite semanal    : ${limit:.2f} USD")
    print(f"• Saldo restante    : ${limit_remaining:.3f} USD")
  else:
    print("• Límite semanal    : Sin límite asignado")

  print("=" * 40 + "\n")

except Exception as e:
  print(f"Error al verificar el saldo: {e}")
