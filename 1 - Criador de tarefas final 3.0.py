import os
import time
import csv
import random
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

# ================== CONFIG ==================
DRIVER_PATH = os.path.join(os.path.dirname(__file__), "msedgedriver.exe")
CSV_PATH = os.path.join(os.path.dirname(__file__), "Banco_Tarefas.csv")
LAST_REQ_FILE = "last_request.txt"
BASE_URL = "https://suporte.ms.gov.br/WorkOrder.do?woMode=viewWO&woID={woid}#tasks"
PROFILE_PATH = r"C:\Users\wfrancischini\AppData\Local\Microsoft\Edge\User Data"

DEBUG_HL = True
LAST_HOURS_FILE = "last_hours.txt"

# ================== UTILS ==================
def highlight(driver, element, color='red', width=3):
    if not DEBUG_HL:
        return
    try:
        driver.execute_script(
            f"arguments[0].style.border = '{width}px solid {color}'",
            element
        )
    except Exception:
        pass

def remove_all_highlights(driver):
    """Remove todos os highlights deixados pelos elementos"""
    try:
        driver.execute_script("""
            // Remover bordas de todos os elementos
            var allElements = document.querySelectorAll('*');
            for (var i = 0; i < allElements.length; i++) {
                allElements[i].style.border = '';
            }
            
            // Remover foco ativo
            if (document.activeElement) {
                document.activeElement.blur();
            }
            
            // Clicar em área neutra do body
            document.body.click();
        """)
    except Exception:
        pass

def salvar_last_req(woid):
    with open(LAST_REQ_FILE, "w", encoding="utf-8") as f:
        f.write(str(woid))

def ler_last_req():
    if not os.path.exists(LAST_REQ_FILE):
        return ""
    with open(LAST_REQ_FILE, encoding="utf-8") as f:
        content = f.read().strip()
        # Se contém "|", extrair apenas o workorder_id (primeira parte)
        if "|" in content:
            return content.split("|")[0]
        return content

def ler_exec_tag():
    """Lê EXEC_TAG do arquivo last_request.txt se disponível"""
    if not os.path.exists(LAST_REQ_FILE):
        return ""
    with open(LAST_REQ_FILE, encoding="utf-8") as f:
        content = f.read().strip()
        # Se contém "|", extrair o exec_tag (segunda parte)
        if "|" in content and len(content.split("|")) >= 2:
            return content.split("|")[1]
        return ""

def espera_xpath(driver, xpath, timeout=1):
    elem = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )
    highlight(driver, elem)
    return elem

def espera_visivel(driver, xpath, timeout=1):
    elem = WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.XPATH, xpath))
    )
    highlight(driver, elem, color='blue')
    return elem

def clica_xpath(driver, xpath, timeout=1):
    elem = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
    highlight(driver, elem, color='green')
    elem.click()
    return elem

def switch_to_task_iframe(driver):
    driver.switch_to.default_content()
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    for frm in frames:
        if frm.get_attribute("id") == "taskmodule_popup-frame":
            driver.switch_to.frame(frm)
            print("Trocou para o iframe taskmodule_popup-frame")
            return
    raise Exception("iframe taskmodule_popup-frame não encontrado!")
# ================== SELECT2 helpers ==================
def _find_select2_container_by_label(driver, label_text, timeout=1):
    container = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((
            By.XPATH,
            f"//label[contains(normalize-space(), '{label_text}')]/ancestor::*[self::div or self::td or self::li][1]"
        ))
    )
    highlight(driver, container, color='orange', width=2)
    return container

def _open_select2_and_get_search(driver, container, timeout=1):
    try:
        trigger = container.find_element(By.CSS_SELECTOR, ".select2-selection")
    except Exception:
        trigger = container.find_element(By.CSS_SELECTOR, ".select2-choice")
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", trigger)
    highlight(driver, trigger, color='green')
    trigger.click()
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".select2-container--open"))
        )
        search_input = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input.select2-search__field"))
        )
    except TimeoutException:
        search_input = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, "//div[contains(@id,'select2-drop')]//input"))
        )
    highlight(driver, search_input, color='blue')
    return search_input

def _click_result_option(driver, value_to_select, timeout=1):
    alvo = (value_to_select or "").strip().lower()

    def coleta_opcoes():
        opts = driver.find_elements(By.CSS_SELECTOR, "li.select2-results__option")
        if not opts:
            opts = driver.find_elements(By.XPATH, "//div[contains(@id,'select2-drop')]//li[contains(@class,'select2-result')]")
        return opts

    end = time.time() + timeout
    last_exc = None
    while time.time() < end:
        try:
            opts = coleta_opcoes()
            if not opts:
                time.sleep(0.2)
                continue
            for o in opts:
                txt = o.text.strip()
                if txt.lower() == alvo:
                    highlight(driver, o, color='green')
                    o.click()
                    break
            else:
                picked = next((o for o in opts if alvo in o.text.strip().lower()), None)
                if picked:
                    highlight(driver, picked, color='green')
                    picked.click()
                else:
                    time.sleep(0.2)
                    continue
            break
        except StaleElementReferenceException as e:
            last_exc = e
            time.sleep(0.25)
        except Exception as e:
            last_exc = e
            time.sleep(0.25)
    else:
        raise TimeoutException(f"Opção '{value_to_select}' não encontrada no Select2. Última exceção: {last_exc}")

    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, ".select2-container--open")) == 0 and
                  len(d.find_elements(By.XPATH, "//div[contains(@id,'select2-drop') and contains(@style,'display: block')]")) == 0
    )

def close_any_open_select2(driver, timeout=1):
    for _ in range(timeout * 2):
        aberto_v4 = driver.find_elements(By.CSS_SELECTOR, ".select2-container--open")
        aberto_v3 = driver.find_elements(By.XPATH, "//div[contains(@id,'select2-drop') and contains(@style,'display: block')]")
        if not aberto_v4 and not aberto_v3:
            return
        try:
            driver.switch_to.active_element.send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(0.25)

def _assert_value_rendered(driver, container, value_to_select):
    rendered = None
    try:
        rendered = container.find_element(By.CSS_SELECTOR, ".select2-selection__rendered")
    except Exception:
        try:
            rendered = container.find_element(By.CSS_SELECTOR, ".select2-chosen")
        except Exception:
            return
    if rendered:
        txt = rendered.text.strip()
        if txt and value_to_select.strip().lower() not in txt.lower():
            raise Exception(f"Select2 não ficou com o valor esperado. Renderizado: '{txt}'")

def select2_by_label(driver, label_text, value_to_select, timeout=1):
    container = _find_select2_container_by_label(driver, label_text, timeout)
    search_input = _open_select2_and_get_search(driver, container, timeout)
    search_input.clear()
    search_input.send_keys(value_to_select)
    _click_result_option(driver, value_to_select, timeout)
    _assert_value_rendered(driver, container, value_to_select)
    try:
        search_input.send_keys(Keys.ESCAPE)
    except Exception:
        pass
    close_any_open_select2(driver, 5)

def select2_fallback_by_open_search_id(driver, search_xpath, value_to_select, timeout=1):
    search_input = espera_visivel(driver, search_xpath, timeout)
    search_input.clear()
    search_input.send_keys(value_to_select)
    _click_result_option(driver, value_to_select, timeout)
    try:
        search_input.send_keys(Keys.ESCAPE)
    except Exception:
        pass
    close_any_open_select2(driver, 5)

# ================== Botão "Adicionar tarefa" ==================
def click_add_task(driver, timeout=1):
    locators = [
        "//a[contains(text(),'Criar nova tarefa')]",
        "//button[contains(@aria-label,'Adicionar tarefa') or contains(@title,'Adicionar tarefa')]",
        "//*[@id='addNewtask']",
        "//*[@id='addNewtask']/span[1]",
        "//span[contains(@class,'common-add-icon4')]/ancestor::*[self::a or self::button][1]"
    ]
    last_exc = None
    for xpath in locators:
        try:
            elem = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
            highlight(driver, elem, color='green')
            if elem.tag_name.lower() == "span":
                parent = elem.find_element(By.XPATH, "./ancestor::*[self::a or self::button][1]")
                highlight(driver, parent, color='green')
                parent.click()
            else:
                elem.click()
            return True
        except Exception as e:
            last_exc = e
            continue
    raise TimeoutException(f"Não encontrei/consigo clicar no botão de adicionar tarefa. Último erro: {last_exc}")
# ================== CSV & lógica de 8 horas ==================
def parse_hours(val):
    if val is None:
        return 0.0
    s = str(val).strip()
    if not s:
        return 0.0
    if ":" in s:
        hh, mm = s.split(":", 1)
        try:
            h = int(hh)
            m = int(mm)
            return h + (m / 60.0)
        except:
            pass
    s = s.replace(",", ".")
    try:
        return float(s)
    except:
        return 0.0

def hours_to_form_input(val):
    s = f"{val:.2f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")

def ler_todas_tarefas_csv():
    out = []
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            row = dict(row)
            row["_tempo_gasto_h"] = parse_hours(row.get("tempo_gasto", "0"))
            row["_tempo_estimado_h"] = parse_hours(row.get("tempo_estimado", "0"))
            out.append(row)
    return out

def escolher_tarefas_para_8h(rows, alvo=8.0, tentativas=2000):
    rows = [r for r in rows if r["_tempo_gasto_h"] > 0]
    if not rows:
        return None
    
    # NOVA LÓGICA: Se alvo <= 2h, usar apenas 1 tarefa
    if alvo <= 2.0:
        # Procurar uma tarefa que possa ser ajustada para o alvo
        for r in rows:
            if r["_tempo_gasto_h"] <= alvo * 1.5:  # Máximo 50% acima do alvo
                # Criar cópia da tarefa ajustada
                tarefa_ajustada = r.copy()
                tarefa_ajustada["_tempo_gasto_h"] = alvo
                tarefa_ajustada["tempo_gasto"] = str(alvo).replace(".", ",")
                tarefa_ajustada["tempo_estimado"] = str(alvo).replace(".", ",")
                return [tarefa_ajustada]
        
        # Se não encontrou, usar a menor tarefa e ajustar
        tarefa_min = min(rows, key=lambda r: r["_tempo_gasto_h"])
        tarefa_ajustada = tarefa_min.copy()
        tarefa_ajustada["_tempo_gasto_h"] = alvo
        tarefa_ajustada["tempo_gasto"] = str(alvo).replace(".", ",")
        tarefa_ajustada["tempo_estimado"] = str(alvo).replace(".", ",")
        return [tarefa_ajustada]
    
    # LÓGICA ORIGINAL: Para > 2h, usar múltiplas tarefas
    for _ in range(tentativas):
        random.shuffle(rows)
        soma = 0.0
        escolhidas = []
        for r in rows:
            h = r["_tempo_gasto_h"]
            if soma + h <= alvo + 1e-9:
                escolhidas.append(r)
                soma += h
                if abs(soma - alvo) < 1e-9:
                    return escolhidas
    return None

# ================== MAIN ==================
def limpa_dec(val):
    v = (val or "").strip()
    return v.replace(".", ",") if v else ""

def salvar_last_hours(hours):
    with open(LAST_HOURS_FILE, "w", encoding="utf-8") as f:
        f.write(str(hours))

def ler_last_hours():
    if not os.path.exists(LAST_HOURS_FILE):
        return "8"
    with open(LAST_HOURS_FILE, encoding="utf-8") as f:
        return f.read().strip()

def click_tasks_tab(driver, timeout=10):
    """Clica na aba Tarefas antes de tentar adicionar uma nova tarefa"""
    try:
        tasks_tab = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='tasks-tab']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", tasks_tab)
        highlight(driver, tasks_tab, color='green')
        tasks_tab.click()
        print("Clicou na aba Tarefas")
        time.sleep(1)  # Aguarda a aba carregar
        return True
    except Exception as e:
        print(f"Erro ao clicar na aba Tarefas: {e}")
        return False

def main():
    # Modo sem prompt quando chamado pelo Flask
    NO_PROMPT = os.getenv("NO_PROMPT", "0") == "1"
    
    # EXEC_TAG para identificação das tarefas criadas
    EXEC_TAG = os.getenv("EXEC_TAG", "")
    # Se não definido via env, tentar ler do arquivo
    if not EXEC_TAG:
        EXEC_TAG = ler_exec_tag()
    
    if EXEC_TAG:
        print(f"[exec] Usando EXEC_TAG: {EXEC_TAG}")

    # --- CHAMADO ---
    ultimo = ler_last_req().strip()
    if NO_PROMPT:
        chamado = ultimo  # usa o que o app já gravou no last_request.txt
        if not chamado:
            print("ID do chamado não informado e last_request.txt está vazio. Abortando.")
            return
        print(f"[web] Usando chamado: {chamado}")
    else:
        chamado = input(f"ID do chamado (Enter para usar o último: {ultimo}): ").strip() or ultimo
        if not chamado:
            print("ID do chamado não informado!")
            return
        salvar_last_req(chamado)

    # --- HORAS ALVO ---
    last_hours = ler_last_hours().strip() or "8"
    if NO_PROMPT:
        horas_str = last_hours  # usa o que o app já gravou no last_hours.txt (ou default 8)
        print(f"[web] Usando horas alvo: {horas_str}")
    else:
        horas_str = input(f"Quantas horas deseja gerar? (Enter para usar o último: {last_hours}): ").strip() or last_hours
        salvar_last_hours(horas_str)

    try:
        horas_alvo = float(horas_str.replace(",", "."))
    except Exception:
        print(f"Valor de horas inválido: '{horas_str}'")
        return
    salvar_last_hours(horas_alvo)

    # --- WebDriver / Navegação ---
    options = webdriver.EdgeOptions()
    options.add_experimental_option("detach", False)  # Permitir fechamento automático
    
    # Usar perfil do usuário para manter logins salvos
    options.add_argument(f'--user-data-dir={PROFILE_PATH}')
    options.add_argument('--profile-directory=Default')
    
    # Opções básicas de estabilidade (sem interferir no perfil)
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-renderer-backgrounding')
    
    # Tentar diferentes estratégias de inicialização
    try:
        print("Tentando inicializar Edge com perfil personalizado...")
        driver = webdriver.Edge(service=Service(DRIVER_PATH), options=options)
    except Exception as e1:
        print(f"Falha com perfil personalizado: {e1}")
        print("Tentando inicializar Edge sem perfil personalizado...")
        
        # Remover opções de perfil e tentar novamente
        options_simple = webdriver.EdgeOptions()
        options_simple.add_experimental_option("detach", False)  # Permitir fechamento automático
        options_simple.add_argument('--no-sandbox')
        options_simple.add_argument('--disable-dev-shm-usage')
        options_simple.add_argument('--disable-gpu')
        options_simple.add_argument('--remote-debugging-port=9222')
        
        try:
            driver = webdriver.Edge(service=Service(DRIVER_PATH), options=options_simple)
        except Exception as e2:
            print(f"Falha sem perfil: {e2}")
            print("Tentando inicializar Edge em modo básico...")
            
            # Última tentativa com opções mínimas
            options_minimal = webdriver.EdgeOptions()
            options_minimal.add_argument('--no-sandbox')
            options_minimal.add_argument('--disable-dev-shm-usage')
            
            driver = webdriver.Edge(service=Service(DRIVER_PATH), options=options_minimal)
    driver.get(BASE_URL.format(woid=chamado))

    time.sleep(2)
    if not click_tasks_tab(driver):
        print("ERRO: Nao foi possivel acessar a aba Tarefas")
        return

    # --- Seleção de tarefas ---
    todas = ler_todas_tarefas_csv()
    selecao = escolher_tarefas_para_8h(todas, alvo=horas_alvo, tentativas=3000)

    if not selecao:
        # Tenta pegar a combinação mais próxima sem ultrapassar
        todas_validas = [r for r in todas if r["_tempo_gasto_h"] > 0]
        if not todas_validas:
            print("ERRO: Não há nenhuma tarefa válida no CSV (campo tempo_gasto deve ser maior que zero). Adicione ou corrija as tarefas no arquivo Banco_Tarefas.csv e tente novamente.")
            return
        todas_validas.sort(key=lambda r: -r["_tempo_gasto_h"])
        soma = 0.0
        escolhidas = []
        for r in todas_validas:
            if soma + r["_tempo_gasto_h"] <= horas_alvo + 1e-9:
                escolhidas.append(r)
                soma += r["_tempo_gasto_h"]
        if escolhidas and soma < horas_alvo:
            # Ajusta o tempo_gasto e tempo_estimado da última tarefa para bater o alvo
            delta = horas_alvo - soma
            nova_hora = escolhidas[-1]["_tempo_gasto_h"] + delta
            escolhidas[-1]["_tempo_gasto_h"] = nova_hora
            escolhidas[-1]["tempo_gasto"] = str(nova_hora).replace(".", ",")
            escolhidas[-1]["tempo_estimado"] = str(nova_hora).replace(".", ",")
            # Atualiza o CSV
            with open(CSV_PATH, "w", encoding="utf-8-sig", newline='') as f:
                fieldnames = todas[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
                writer.writeheader()
                for row in todas:
                    if row["titulo"] == escolhidas[-1]["titulo"]:
                        row["tempo_gasto"] = escolhidas[-1]["tempo_gasto"]
                        row["tempo_estimado"] = escolhidas[-1]["tempo_estimado"]
                    writer.writerow(row)
            selecao = escolhidas
            print(f"AVISO: Ajustei o tempo_gasto e tempo_estimado da última tarefa para totalizar {horas_alvo}h.")
        elif not escolhidas:
            # Se não conseguiu nenhuma combinação, ajusta a tarefa com menor tempo_gasto
            tarefa_min = min(todas_validas, key=lambda r: r["_tempo_gasto_h"])
            tarefa_min["_tempo_gasto_h"] = horas_alvo
            tarefa_min["tempo_gasto"] = str(horas_alvo).replace(".", ",")
            tarefa_min["tempo_estimado"] = str(horas_alvo).replace(".", ",")
            # Atualiza o CSV
            with open(CSV_PATH, "w", encoding="utf-8-sig", newline='') as f:
                fieldnames = todas[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
                writer.writeheader()
                for row in todas:
                    if row["titulo"] == tarefa_min["titulo"]:
                        row["tempo_gasto"] = tarefa_min["tempo_gasto"]
                        row["tempo_estimado"] = tarefa_min["tempo_estimado"]
                    writer.writerow(row)
            selecao = [tarefa_min]
            print(f"AVISO: Não foi possível formar uma combinação. Ajustei a tarefa '{tarefa_min['titulo']}' para {horas_alvo}h.")
        else:
            print(f"AVISO: Nao foi possivel formar exatamente {horas_alvo}h com as tarefas unicas do CSV.")
            print("Ajuste os valores de 'tempo_gasto' no CSV (ex.: 2, 1.5, 0.5, etc.) para permitir combinacoes.")
            return

    print(f"Selecionadas {len(selecao)} tarefas aleatórias (sem repetição) totalizando {horas_alvo}h.")

    time.sleep(1.2)
    click_add_task(driver, timeout=1)
    time.sleep(0.8)

    switch_to_task_iframe(driver)
    espera_visivel(driver, "//*[@id='task-container']")
    
    for idx, tarefa in enumerate(selecao):
        print(f"Preenchendo: {tarefa.get('titulo','(sem título)')}  [{tarefa['_tempo_gasto_h']}h]")

        # TÍTULO (sem EXEC_TAG - título limpo)
        campo_titulo = espera_visivel(driver, "//*[@id='for_title']", 25)
        driver.execute_script("arguments[0].focus();", campo_titulo)
        campo_titulo.clear()
        campo_titulo.send_keys(tarefa.get("titulo", ""))

        # DESCRIÇÃO
        inner_iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if inner_iframes:
            driver.switch_to.frame(inner_iframes[0])
        desc_body = espera_visivel(driver, "//body[contains(@class,'ze_body') or @class='ze_body' or contains(@class,'editable')]", 15)
        desc_body.click()
        
        # Descrição com EXEC_TAG discreto oculto no final (apenas para busca SQL)
        descricao_original = tarefa.get("descricao", "")
        if EXEC_TAG:
            # Extrair apenas os últimos 4 dígitos + seta para ser mais discreto
            tag_discreto = EXEC_TAG[-4:] + " -->"
            descricao_com_tag = f"{descricao_original}{tag_discreto}"
        else:
            descricao_com_tag = descricao_original
            
        desc_body.send_keys(descricao_com_tag)
        driver.switch_to.parent_frame()

        # Volta para o iframe do modal de tarefa
        switch_to_task_iframe(driver)

        # GRUPO
        start = time.time()
        select2_by_label(driver, "Grupo", "CSI EAST")
        elapsed = time.time() - start
        print(f"[Teste 1] Tempo para preencher o campo 'Grupo': {elapsed:.2f} segundos")

        # PROPRIETÁRIO
        select2_by_label(driver, "Proprietário", "Willian Alvaro Francischini")

        # Fecha overlays do select2 antes dos tempos
        close_any_open_select2(driver, 3)

        # TEMPO ESTIMADO
        est = espera_visivel(driver, "//*[@id='for_udf_fields_sline_tempo_estimado']", 25)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", est)
        est.clear()
        est_val = tarefa.get("tempo_estimado")
        if not est_val or not est_val.strip():
            est_val = hours_to_form_input(tarefa["_tempo_gasto_h"])
        est.send_keys(limpa_dec(est_val))

        # TEMPO GASTO
        gst = espera_visivel(driver, "//*[@id='for_udf_fields_sline_tempo_gasto']", 25)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", gst)
        gst.clear()
        gst.send_keys(hours_to_form_input(tarefa["_tempo_gasto_h"]))

        # COMPLEXIDADE
        try:
            select2_by_label(driver, "Complexidade", tarefa.get("complexidade", "Baixa"))
        except Exception as e1:
            print(f"[aviso] Select2 por label falhou, tentando fallback direto: {e1}")
            try:
                container = _find_select2_container_by_label(driver, "Complexidade", 10)
                try:
                    trigger = container.find_element(By.CSS_SELECTOR, ".select2-selection")
                except Exception:
                    trigger = container.find_element(By.CSS_SELECTOR, ".select2-choice")
                trigger.click()
            except Exception:
                pass
            select2_fallback_by_open_search_id(driver, "//*[@id='s2id_autogen14_search']", tarefa.get("complexidade", "Baixa"), 10)

        # STATUS: Fechado
        try:
            select2_by_label(driver, "Status", "Fechado")
        except Exception as e:
            print(f"[aviso] Falha ao selecionar 'Fechado' no campo Status: {e}")

        time.sleep(0.5)
        clica_xpath(driver, "//*[@id='task-container']//button[contains(text(),'Salvar')]", 15)

        WebDriverWait(driver, 20).until_not(
            EC.presence_of_element_located((By.XPATH, "//*[@id='task-container']//button[contains(text(),'Salvar')]"))
        )
        driver.switch_to.default_content()
        print("==>> Tarefa criada!")

        # Só prepara nova tarefa se NÃO for a última (usando índice)
        is_last_task = (idx == len(selecao) - 1)
        
        if not is_last_task:
            time.sleep(0.8)
            click_add_task(driver, timeout=1)
            time.sleep(0.8)
            switch_to_task_iframe(driver)
        else:
            # É a última tarefa - garantir que estamos no contexto principal limpo
            print("INFO: Última tarefa concluída - preparando finalização...")
            driver.switch_to.default_content()
            time.sleep(2)  # Aguardar estabilização

    print(f"SUCESSO: Todas as tarefas do dia foram criadas somando exatamente {horas_alvo}h.")
    
    # Finalizar na aba Tarefas para mostrar o resultado visual
    try:
        print("INFO: Finalizando na aba Tarefas para visualização do resultado...")
        
        # Garantir contexto limpo
        driver.switch_to.default_content()
        time.sleep(1)
        
        # PRIMEIRO: Remover TODOS os highlights deixados durante a execução
        remove_all_highlights(driver)
        time.sleep(1)
        
        # Clicar na aba "Tarefas" para mostrar as tarefas criadas
        tarefas_tab = driver.find_element(By.XPATH, "//a[contains(@class, 'tab') and contains(text(), 'Tarefas')]")
        tarefas_tab.click()
        time.sleep(2)
        
        # SEGUNDO: Remover highlights novamente após mudança de aba
        remove_all_highlights(driver)
        
        print("INFO: ✅ Finalizado na aba Tarefas - você pode visualizar as tarefas criadas!")
        print("INFO: As tarefas foram criadas com sucesso e estão visíveis na tela.")
        
        # Aguardar 5 segundos para o usuário ver o resultado
        print("INFO: Aguardando 5 segundos para visualização das tarefas...")
        time.sleep(5)
        
    except Exception as e:
        print(f"AVISO: Não foi possível navegar para a aba Tarefas: {e}")
        print("INFO: As tarefas foram criadas com sucesso, mas navegue manualmente para a aba Tarefas.")
    
    # Fechar o navegador automaticamente
    try:
        print("INFO: Fechando o navegador automaticamente...")
        driver.quit()
        print("INFO: ✅ Navegador fechado com sucesso!")
    except Exception as e:
        print(f"AVISO: Erro ao fechar navegador: {e}")
    
    print("INFO: Script finalizado com sucesso!")

if __name__ == "__main__":
    main()
