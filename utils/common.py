
import streamlit as st
import pandas as pd
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta, timezone
from functools import lru_cache

# ============== Carregamento de GeoJSON e dados (Cacheados) ================
@lru_cache(maxsize=None)
def load_geojson_data():
    """Carrega os arquivos GeoJSON e retorna um dicionário com os dados."""
    files = {
        "trechos_perene.geojson": "geojson_trechos",
        "Açudes_Monitorados.geojson": "geojson_acudes",
        "Sedes_Municipais.geojson": "geojson_sedes",
        "c_gestoras.geojson": "geojson_c_gestoras",
        "poligno_municipios.geojson": "geojson_poligno",
        "bacia_banabuiu.geojson": "geojson_bacia",
        "pontos_controle.geojson": "geojson_pontos",
        "situa_municipio.geojson": "geojson_situa",
    }
    data = {}
    for filename, var_name in files.items():
        filepath = os.path.join("data", filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data[var_name] = json.load(f)
        except FileNotFoundError:
            st.warning(f"Arquivo GeoJSON não encontrado: {filename}. O mapa pode não renderizar corretamente.")
            data[var_name] = {}
        except json.JSONDecodeError:
            st.error(f"Erro ao decodificar JSON do arquivo: {filename}. Verifique a formatação do arquivo.")
            data[var_name] = {}
    return data

@st.cache_data(ttl=300)
def carregar_dados_vazoes():
    """Carrega os dados de vazão do Google Sheets."""
    try:
        url = "https://docs.google.com/spreadsheets/d/1pbNcZ9hS8DhotdkYuPc8kIOy5dgyoYQb384-jgqLDfA/export?format=csv"
        df = pd.read_csv(url)
        df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
        df["Mês"] = df["Data"].dt.to_period("M").astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados de vazões: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_reservatorios_data():
    """Carrega os dados dos reservatórios do Google Sheets."""
    try:
        url = "https://docs.google.com/spreadsheets/d/1zZ0RCyYj-AzA_dhWzxRziDWjgforbaH7WIoSEd2EKdk/export?format=csv"
        df = pd.read_csv(url)
        # Normalizações de tipo
        if {"Latitude", "Longitude"} <= set(df.columns):
            df["Latitude"] = pd.to_numeric(df["Latitude"].astype(str).str.replace(",", "."), errors="coerce")
            df["Longitude"] = pd.to_numeric(df["Longitude"].astype(str).str.replace(",", "."), errors="coerce")
            df = df.dropna(subset=["Latitude", "Longitude"])
        else:
            st.error("Colunas 'Latitude' e 'Longitude' são necessárias.")
            return pd.DataFrame()
        
        if "Data de Coleta" in df.columns:
            df["Data de Coleta"] = pd.to_datetime(df["Data de Coleta"], errors="coerce", dayfirst=True)
            df = df.dropna(subset=["Data de Coleta"])

        converters = {
            "Percentual": lambda s: pd.to_numeric(s.astype(str).str.replace(",", ".").str.replace("%", "").str.strip(), errors="coerce"),
            "Volume": lambda s: pd.to_numeric(s.astype(str).str.replace(",", ".").str.strip(), errors="coerce"),
            "Cota Sangria": lambda s: pd.to_numeric(s.astype(str).str.replace(",", ".").str.strip(), errors="coerce"),
            "Nivel": lambda s: pd.to_numeric(s.astype(str).str.replace(",", ".").str.strip(), errors="coerce"),
        }
        for col, conv in converters.items():
            if col in df.columns:
                df[col] = conv(df[col])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados de reservatórios: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_docs_data():
    """Carrega os dados de documentos do Google Sheets."""
    SHEET_ID = "1-Tn_ZDHH-mNgJAY1WtjWd_Pyd2f5kv_ZU8dhL0caGDI"
    GID = "0"
    URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
    try:
        df = pd.read_csv(URL, encoding="utf-8-sig").dropna(how="all")
        for col in ["Operação", "Data da Reunião", "Reservatório/Sistema", "Local da Reunião", "Parâmetros aprovados", "Vazão média"]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_simulacoes_data():
    """Carrega os dados de simulações do Google Sheets."""
    sheet_url = "https://docs.google.com/spreadsheets/d/1C40uaNmLUeu-k_FGEPZOgF8FwpSU00C9PtQu8Co4AUI/export?format=csv"
    try:
        df = pd.read_csv(sheet_url, sep=',', decimal=',')
    except Exception as e:
        st.error(f"Não foi possível ler a planilha de simulações: {e}")
        return pd.DataFrame()

    colunas = ["Data", "Açude", "Município", "Região Hidrográfica", "Cota Inicial (m)", "Cota Dia (m)", "Volume (m³)",
                "Volume (%)", "Evapor. Parcial (mm)", "Cota Interm. (m)", "Volume Interm. (m³)",
                "Liberação (m³/s)", "Liberação (m³)", "Volume Final (m³)", "Cota Final (m)", "Coordendas"]
    faltantes = [c for c in colunas if c not in df.columns]
    if faltantes:
        st.error(f"As seguintes colunas não foram encontradas na planilha de simulações: {', '.join(faltantes)}")
        return pd.DataFrame()
    df = df[colunas].copy()
    df["Data"] = pd.to_datetime(df["Data"].astype(str).str.strip(), dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Data"])
    colunas_numericas = ["Cota Inicial (m)", "Cota Dia (m)", "Volume (m³)", "Volume (%)", "Evapor. Parcial (mm)"]
    for col in colunas_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    def formatar_volume(volume):
        if volume >= 1_000_000:
            return f"{volume / 1_000_000:,.2f} milhões/m³".replace(",", "X").replace(".", ",").replace("X", ".")
        elif volume > 0:
            return f"{volume / 1_000:,.2f} mil/m³".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            return "0 m³"
    df['Volume_formatado'] = df['Volume (m³)'].apply(formatar_volume)
    return df

def convert_vazao(series, unidade):
    """Converte vazão entre L/s e m³/s."""
    if unidade == "m³/s":
        return series / 1000.0, "m³/s"
    return series, "L/s"

def render_header():
    """Renderiza o cabeçalho personalizado da aplicação."""
    fuso_brasilia = timezone(timedelta(hours=-3))
    agora = datetime.now(fuso_brasilia)
    dias_semana = {"Monday": "Segunda-feira", "Tuesday": "Terça-feira", "Wednesday": "Quarta-feira", "Thursday": "Quinta-feira", "Friday": "Sexta-feira", "Saturday": "Sábado", "Sunday": "Domingo"}
    meses = {"January": "janeiro", "February": "fevereiro", "March": "março", "April": "abril", "May": "maio", "June": "junho", "July": "julho", "August": "agosto", "September": "setembro", "October": "outubro", "November": "novembro", "December": "dezembro"}
    data_hoje = f"{dias_semana[agora.strftime('%A')]}, {agora.day:02d} de {meses[agora.strftime('%B')]} de {agora.year}"

    st.markdown(
        f"""
        <style>
        [data-testid="stHeader"]{{visibility:hidden;}}
        .custom-header{{position:fixed;top:0;left:0;width:100vw;
        left:50%;right:50%;margin-left:-50vw;margin-right:-50vw;
        background:linear-gradient(135deg,#228B22 0%,#006400 50%,#004d00 100%);
        color:white;padding:8px 5%;font-family:'Segoe UI',Roboto,sans-serif;
        box-shadow:0 4px 12px rgba(0,0,0,.1);z-index:9999}}
        .header-container{{max-width:1200px;margin: 8px auto;display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:10px}}
        .header-brand{{display:flex;align-items:center;gap:10px;flex:1;min-width:200px}}
        .header-logo{{height:36px;filter:drop-shadow(0 2px 2px rgba(0,0,0,.2))}}
        .header-title{{font-size:clamp(14px,3vw,18px);font-weight:600;letter-spacing:.5px;text-shadow:0 1px 3px rgba(0,0,0,.3)}}
        .header-date{{background:rgba(255,255,255,.15);padding:4px 10px;border-radius:20px;font-size:clamp(10px,2.5vw,13px);font-weight:500;display:flex;align-items:center;gap:6px;backdrop-filter:blur(5px);white-space:nowrap}}
        .header-links{{display:flex;align-items:center;gap:15px}}
        .dropdown{{position:relative;display:inline-block}}
        .dropdown-content{{display:none;position:absolute;background-color:#006400;min-width:160px;box-shadow:0 8px 16px rgba(0,0,0,0.2);z-index:1;border-radius:8px;padding:8px 0}}
        .dropdown:hover .dropdown-content{{display:block}}
        .dropdown-btn{{background:rgba(255,255,255,0.1);border:none;color:white;padding:8px 12px;border-radius:20px;cursor:pointer;display:flex;align-items:center;gap:5px;font-size:13px}}
        .dropdown-btn:hover{{background:rgba(255,255,255,0.2)}}
        .dropdown-content a{{color:white;padding:8px 16px;text-decoration:none;display:block;font-size:13px}}
        .dropdown-content a:hover{{background-color:#004d00}}
        .main .block-container{{padding-top:50px;}}
        .filter-card{{border:1px solid #e6e6e6;border-radius:1px;padding:1px 1px;background:#fff;box-shadow:0 4px 14px rgba(0,0,0,.06);margin-top:6px}}
        .filter-title{{font-weight:600;margin-bottom:6px}}
        .quick-chips span{{display:inline-block;border:1px solid #dcdcdc;border-radius:999px;padding:4px 10px;margin-right:6px;margin-top:4px;cursor:pointer;font-size:12px}}
        .quick-chips span:hover{{background:#f5f5f5}}
        .kpi-card{{border:1px solid #eaeaea;border-radius:14px;padding:14px;background:linear-gradient(180deg,#ffffff 0%, #fafafa 100%);box-shadow:0 6px 16px rgba(0,0,0,.06);text-align:center}}
        .kpi-value{{font-size:22px;font-weight:700;margin-top:4px}}
        .st-emotion-cache-1q7spjk{{color:#228B22!important;font-weight:bold}}
        .st-emotion-cache-1q7spjk:hover{{color:#006400!important}}
        .map-style-selector{{margin-top:-10px}}
        @media(max-width:600px){{
        .main .block-container{{padding-top:110px}}
        .header-links{{gap:10px}}
        .dropdown-btn{{padding:6px 10px}}
        }}
        </style>
        <div class="custom-header">
        <div class="header-container">
            <div class="header-brand">
            <img src="https://i.ibb.co/KpHGQ6qg/LOGOPROTAL.png" class="header-logo" style="width: 45px; height: auto;">
            <div>
                <div class="header-title">Portal Transparência e Participação</div>
                <div style="opacity:.9;font-size:13px">📌Comitê da Sub-Bacia do Rio Banabuiu</div>
            </div>
            </div>
            <div class="header-links">
            <div class="dropdown">
                <button class="dropdown-btn">Sistema<span>▼</span></button>
                <div class="dropdown-content">
                <a href="https://www.srh.ce.gov.br/" target="_blank" rel="noopener">🏢 SRH</a>
                <a href="https://www.sohidra.ce.gov.br/" target="_blank" rel="noopener">💧 COGERH</a>
                <a href="https://www.sohidra.ce.gov.br/" target="_blank" rel="noopener">🚰 SOHIDRA</a>
                <a href="https://www.funceme.br/" target="_blank" rel="noopener">🌦️ FUNCEME</a>
                </div>
            </div>
            <div class="dropdown">
                <button class="dropdown-btn">Comitê<span>▼</span></button>
                <div class="dropdown-content">
                <a href="https://www.cbhbanabuiu.com.br/institucional/" target="_blank" rel="noopener">💼 Institucional</a>
                <a href="https://www.cbhbanabuiu.com.br/institucional/Regimento/" target="_blank" rel="noopener">📃 Regimento</a>
                <a href="https://www.cbhbanabuiu.com.br/institucional/conheca-nossa-bacia-hidrografica/" target="_blank" rel="noopener">💦 A Bacia</a>
                </div>
            </div>
            <div class="header-date">📅 {data_hoje}</div>
            </div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_footer():
    """Renderiza o rodapé da aplicação."""
    st.markdown(
        f"""
        <style>
        .footer-mobile-full {{
            position: relative;
            width: 100vw;
            left: 50%;
            right: 50%;
            margin-left: -50vw;
            margin-right: -50vw;
            margin-top: 40px;
            background: none;
            color: #000000;
            padding: 10px 0;
            font-family: 'Segoe UI', Roboto, sans-serif;
            border-top: 3px solid #fad905;
            text-align: center;
            box-shadow: none;
        }}
        .footer-content {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            width: 90%;
            margin: 0 auto;
            position: relative;
        }}
        .footer-row {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
            gap: 12px;
        }}
        .footer-item {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 14px;
        }}
        .footer-divider {{
            color: rgba(0,0,0,0.4);
            font-size: 14px;
        }}
        .footer-address {{
            font-size: 13px;
            opacity: 0.9;
            margin-top: 4px;
        }}
        .footer-logos {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
            margin-top: 10px;
        }}
        .footer-logos img {{
            height: 60px;
        }}
        /* Botão Voltar ao Topo */
        .back-to-top {{
            position: absolute;
            right: 20px;
            bottom: 20px;
            background-color: #fad905;
            color: #000;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            font-size: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }}
        .back-to-top:hover {{
            background-color: #e6c800;
            transform: translateY(-2px);
        }}
        /* Mobile First */
        @media (min-width: 481px) {{
            .footer-row {{
                gap: 16px;
            }}
            .footer-item {{
                font-size: 15px;
            }}
        }}
        @media (max-width: 480px) {{
            .footer-row {{
                flex-direction: column;
                gap: 8px;
            }}
            .footer-divider {{
                display: none;
            }}
            .footer-item {{
                font-size: 13px;
            }}
            .footer-address {{
                font-size: 12px;
            }}
            .footer-logos img {{
                height: 50px;
            }}
            .back-to-top {{
                right: 10px;
                bottom: 10px;
                width: 35px;
                height: 35px;
                font-size: 18px;
            }}
        }}
        </style>
        <div class="footer-mobile-full">
            <div class="footer-content">
                <div class="footer-logos">
                    <img src="https://i.ibb.co/r2FRGkmB/cogerh-logo.png" alt="COGERH Logo">
                    <img src="https://i.ibb.co/tpQrmPb0/csbh.png" alt="CSBH Logo">
                </div>
                <div class="footer-row">
                    <div class="footer-item">
                        <b>Secretaria Executiva do CSBH Banabuiú: COGERH – Gerência da Bacia do Banabuiú</b>
                    </div>
                </div>
                <div class="footer-row">
                    <div class="footer-item">
                        📧 comite.banabuiu@cogerh.com.br 
                    </div>
                    <span class="footer-divider">|</span>
                    <div class="footer-item">
                        📞 (85) 3513-9055
                    </div>
                </div>
                <div class="footer-address">
                    🏢 Rua Dona Francisca Santiago, 44 – Centro. CEP 63800-000 – Quixeramobim/CE
                </div>
                <button class="back-to-top" id="backToTopBtn2">↑</button>
            </div>
        </div>
        <script>
        document.getElementById("backToTopBtn2").addEventListener("click", function() {{
            window.scrollTo({{
                top: 0,
                behavior: 'smooth'
            }});
        }});
        </script>
        """,
        unsafe_allow_html=True,
    )

def salvar_em_planilha(dados_formulario):
    """
    Salva os dados do formulário em uma planilha do Google Sheets.
    """
    try:
        # Credenciais do Google Sheets (lendo do secrets.toml)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"],
                                                                 ["https://spreadsheets.google.com/feeds",
                                                                  "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)

        planilha = client.open_by_key("1aEzpFdPz2lbG7IM9OMIFqVCUtEVkqV18JaytGTX9ugs")
        aba = planilha.worksheet("Página1") 

        dados_formulario['data_envio'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        linha = [
            dados_formulario.get('data_envio', ''),
            dados_formulario.get('nome', ''),
            dados_formulario.get('email', ''),
            dados_formulario.get('telefone', ''),
            dados_formulario.get('cpf_cnpj', ''),
            dados_formulario.get('cidade_estado', ''),
            dados_formulario.get('tipo_contato', ''),
            dados_formulario.get('outro_contato', ''),
            dados_formulario.get('assunto', ''),
            dados_formulario.get('descricao', ''),
            dados_formulario.get('canal_resposta', ''),
            'Sim' if dados_formulario.get('lgpd_consentimento') else 'Não',
            'Sim' if dados_formulario.get('receber_informativos') else 'Não',
        ]
        
        aba.append_row(linha)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar na planilha: {e}")
        return False







