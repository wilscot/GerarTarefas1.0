# Versão 2.2 — Gerador de tarefas VMware com ordenação e atividades fixas
import os, csv, random
from datetime import datetime

def fmt_num(v):
    try: return f"{float(str(v).replace(',','.')):.1f}".replace('.',',')
    except: return '0,0'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

RESOURCE_POOLS = [
    "HP DL360 G10-01 - HIGH", "HP DL360 G10-01 - Normal", "HP DL360 G10-01 - Low",
    "DELL R650 - HIGH", "DELL R650 - Normal", "DELL R650 - Low"
]

STORAGES = ["Storage A", "Storage B", "Storage C", "Storage D"]

# 🔁 LINHAS 25–60: MODELOS dinâmicos + atividades fixas
MODELOS = [
    {
        "titulo": lambda: f"Redistribuir VMs entre {random.choice(STORAGES)} e {random.choice(STORAGES)}",
        "descricao": lambda: f"Realizar DRS manual movendo VMs dos datastores de {random.choice(STORAGES)} para {random.choice(STORAGES)} visando balanceamento de carga.",
        "requires_host": False
    },
    {
        "titulo": lambda: f"Realocar VMs para {random.choice(RESOURCE_POOLS)}",
        "descricao": lambda: f"Mover VMs de criticidade alta para o resource pool {random.choice(RESOURCE_POOLS)} conforme política de desempenho.",
        "requires_host": False
    },
    {
        "titulo": lambda: "Migrar VMs entre datastores",
        "descricao": lambda: f"Executar Storage vMotion para mover VMs da {random.choice(STORAGES)} para a {random.choice([s for s in STORAGES if s != STORAGES[0]])}, otimizando uso de espaço e desempenho.",
        "requires_host": False
    }
]

# 🔁 Adicionando atividades fixas — versão 2.2
MODELOS += [
    {"titulo": "Verificar saúde de hosts com vCenter",
     "descricao": lambda hosts: f"Checar status de CPU, rede, memória e alarmes nos hosts: {hosts}.",
     "requires_host": True},
    {"titulo": "Executar análise de logs ESXi/vRealize",
     "descricao": lambda hosts: f"Extrair e revisar logs críticos de ESXi e vCenter nos hosts: {hosts}.",
     "requires_host": True},
    {"titulo": "Aplicar patch de segurança ESXi",
     "descricao": lambda hosts: f"Aplicar patch via vCenter e validar reinicialização segura nos hosts: {hosts}.",
     "requires_host": True},
    {"titulo": "Migrar VMs via Storage vMotion",
     "descricao": lambda hosts: f"Mover VMs entre datastores para balanceamento de carga nos hosts: {hosts}.",
     "requires_host": True},
    {"titulo": "Verificar compliance de Host Profile",
     "descricao": lambda hosts: f"Ajustar compliance de Host Profiles nos hosts: {hosts}.",
     "requires_host": True},
    {"titulo": "Coletar dados com vRealize Log Insight",
     "descricao": lambda: "Usar vRLI para coletar métricas e analisar tendências de performance.",
     "requires_host": False},
    {"titulo": "Atualizar planilha Linha de crescimento Storage",
     "descricao": lambda: "Atualizar planilha com os campos 'Espaço Utilizado' das storages; calcular média se houver múltiplos pools.",
     "requires_host": False},
    {"titulo": "Reunião com COTIN sobre virtualização",
     "descricao": lambda: "Discutir com Uglaybe problemas da infraestrutura virtual.",
     "requires_host": False},
    {"titulo": "Gerar relatório de servidores da DPGE",
     "descricao": lambda: "Listar VMs alocadas na DPGE.",
     "requires_host": False},
    {"titulo": "Estudar viabilidade da plataforma Nutanix",
     "descricao": lambda: "Avaliar viabilidade técnica de uso de ambiente Nutanix.",
     "requires_host": False},
    {"titulo": "Avaliar viabilidade do vRealize Log Insight",
     "descricao": lambda: "Analisar viabilidade de uso do vRLI na infraestrutura atual.",
     "requires_host": False},
    {"titulo": "Avaliar viabilidade do Veeam Backup",
     "descricao": lambda: "Analisar se Veeam Backup & Replication atende à proteção das VMs.",
     "requires_host": False},
    {"titulo": "Avaliar viabilidade do NetBackup IBM",
     "descricao": lambda: "Avaliar se NetBackup IBM se integra bem com VMware.",
     "requires_host": False},
    {"titulo": "Avaliar viabilidade do VxRail",
     "descricao": lambda: "Analisar uso do Dell VxRail como plataforma HCI.",
     "requires_host": False},
    {"titulo": "Avaliar viabilidade do VMware vSAN",
     "descricao": lambda: "Analisar possibilidade de uso do VMware vSAN.",
     "requires_host": False},
    {"titulo": "Avaliar viabilidade do Harvester",
     "descricao": lambda: "Analisar Harvester como solução de virtualização Kubernetes.",
     "requires_host": False},
    {"titulo": "Avaliar viabilidade do OpenShift Virtualization",
     "descricao": lambda: "Analisar OpenShift Virtualization como camada de VM em K8s.",
     "requires_host": False}
]

def gerar_hosts(max_hosts=5, usados_hosts=set()):
    while True:
        hosts = random.sample(range(1, 1500), k=random.randint(1, max_hosts))
        host_str = ", ".join(f"S{h:04d}.MS" for h in hosts)
        if host_str not in usados_hosts:
            usados_hosts.add(host_str)
            return host_str

def gerar_banco(total=100, max_hosts=5):
    banco = []
    usados_tarefas = set()
    usados_hosts = set()

    while len(banco) < total:
        modelo = random.choice(MODELOS)
        titulo = modelo["titulo"]() if callable(modelo["titulo"]) else modelo["titulo"]
        if modelo["requires_host"]:
            hosts = gerar_hosts(max_hosts, usados_hosts)
            descricao = modelo["descricao"](hosts)
        else:
            descricao = modelo["descricao"]() if callable(modelo["descricao"]) else modelo["descricao"]

        if (titulo, descricao) in usados_tarefas:
            continue
        usados_tarefas.add((titulo, descricao))

        est = round(random.uniform(0.7, 2.5), 1)
        gst = round(est * random.uniform(0.85, 0.95), 1)
        comp = "Baixa" if est <= 1 else ("Alta" if est >= 2 else "Média")

        banco.append({
            "titulo": titulo,
            "descricao": descricao,
            "tempo_estimado": fmt_num(est),
            "tempo_gasto": fmt_num(gst),
            "complexidade": comp
        })

    return banco

# 🔁 LINHAS 100–110: salvar_csv com ordenação por título
def salvar_csv(banco):
    banco_ordenado = sorted(banco, key=lambda x: x["titulo"].lower())
    fname = f"tarefas_vmware_v2_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    path = os.path.join(SCRIPT_DIR, fname)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["titulo", "descricao", "tempo_estimado", "tempo_gasto", "complexidade"])
        for t in banco_ordenado:
            w.writerow([t["titulo"], t["descricao"], t["tempo_estimado"], t["tempo_gasto"], t["complexidade"]])
    print("✅ CSV salvo:", path, "|", len(banco_ordenado), "tarefas")


if __name__ == "__main__":
    banco = gerar_banco(100)
    salvar_csv(banco)