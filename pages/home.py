import streamlit as st

def render_home():
    """
    Renderiza a página inicial de boas-vindas da aplicação.
    """    
#===================TEXTO BOAS VINDAS
    st.markdown(
        """        
        <div style="width: 100%; margin: 0; padding: 0;">
            <img src="https://i.ibb.co/fzQsqPSJ/LOGOSISTEMA.png" 
                 alt="Logo Portal" 
                 style="width: 100%; height: auto; display: block;">
        </div>
        <hr style="border: 0; height: 2px; background: #ddd; margin: 20px auto;">
    
        <div style="background: linear-gradient(135deg, #f0f4f8 0%, #d9e2eb 100%); border-radius: 15px; padding: 30px; border: 1px solid #cdd5e0; box-shadow: 0 6px 15px rgba(0,0,0,0.1); margin-bottom: 30px; text-align: center;">
            <p style="font-family: 'Segoe UI', Arial, sans-serif; color: #2c3e50; font-size: 18px; line-height: 1.8; margin: 0;">
                Este portal foi desenvolvido para fornecer informações e dados em tempo real sobre a bacia do Banabuiú.<br>
                Utilize as abas no topo da página para navegar entre as seções.
            </p>
            <hr style="border: 0; height: 1px; background: #ddd; margin: 20px auto;">
            <div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 16px; color: #5a7d9a;">
                Conteúdo disponível:
                <ul style="list-style-type: none; padding: 0; margin-top: 10px;">
                    <li style="margin: 5px 0;">💧 Painel da Operação: Gráficos e dados de vazão.</li>
                    <li style="margin: 5px 0;">🗺️ Açudes Monitorados: Mapa e dados detalhados.</li>
                    <li style="margin: 5px 0;">📈 Situação das Sedes: Gráficos de cota e volume.</li>
                    <li style="margin: 5px 0;">💬 Alocação Negociada: Atas e apresentações para download.</li>
                    <li style="margin: 5px 0;">🙋🏽 O Comitê: Conheça o Comitê.</li>
                    <li style="margin: 5px 0;">📚 Publicações/Acervo: Publicações que tem relação com Comitê.</li>
                    <li style="margin: 5px 0;">📝 Acompanhamento Diário: A situação diária dos reservatórios.</li>
                    <li style="margin: 5px 0;">✉️ Fale Conosco: Entre em contato.</li>
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.info("👆 Acesse as outras páginas clicando nas abas no topo da tela.", icon="ℹ️")














