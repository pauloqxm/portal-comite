
import json
from datetime import datetime, timedelta, timezone
import streamlit as st

def render_header():
    # Data formatada pt-BR
    fuso_brasilia = timezone(timedelta(hours=-3))
    agora = datetime.now(fuso_brasilia)
    dias_semana = {
        "Monday": "Segunda-feira", "Tuesday": "Terça-feira", "Wednesday": "Quarta-feira",
        "Thursday": "Quinta-feira", "Friday": "Sexta-feira", "Saturday": "Sábado", "Sunday": "Domingo"
    }
    meses = {
        "January": "janeiro", "February": "fevereiro", "March": "março", "April": "abril",
        "May": "maio", "June": "junho", "July": "julho", "August": "agosto",
        "September": "setembro", "October": "outubro", "November": "novembro", "December": "dezembro"
    }
    data_hoje = f"{dias_semana[agora.strftime('%A')]}, {agora.day:02d} de {meses[agora.strftime('%B')]} de {agora.year}"

    st.markdown(
        f"""
        <style>
        [data-testid="stHeader"]{{visibility:hidden;}}
        .custom-header{{position:fixed;top:0;left:0;width:100%;
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
        .main .block-container{{padding-top:90px}}
        @media(max-width:600px){{
         .main .block-container{{padding-top:110px}}
        }}
        </style>
        <div class="custom-header">
          <div class="header-container">
            <div class="header-brand">
              <img src="https://cdn-icons-png.flaticon.com/512/1006/1006363.png" class="header-logo">
              <div>
                <div class="header-title">Acompanhamento da Operação</div>
                <div style="opacity:.9;font-size:13px">📌 Bacia do Banabuiu</div>
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

def load_geojsons():
    """Carrega arquivos .geojson do diretório raiz do app."""
    files = [
        ("trechos_perene.geojson", "trechos"),
        ("Açudes_Monitorados.geojson", "acudes"),
        ("Sedes_Municipais.geojson", "sedes"),
        ("c_gestoras.geojson", "gestoras"),
        ("poligno_municipios.geojson", "poligno"),
        ("bacia_banabuiu.geojson", "bacia"),
        ("pontos_controle.geojson", "pontos"),
    ]
    data = {}
    for fname, key in files:
        try:
            with open(fname, "r", encoding="utf-8") as f:
                data[key] = json.load(f)
        except FileNotFoundError:
            data[key] = None
    return data
