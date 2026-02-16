import streamlit as st
import anthropic
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AI Customer Health Monitor",
    page_icon="🎯",
    layout="wide"
)

def analyze_customer_with_ai(customer_data):
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    prompt = f"""
    Analiza este cliente B2B y proporciona un análisis detallado como Customer Success Manager experto.
    
    Datos del cliente:
    - Nombre: {customer_data['name']}
    - Días desde última actividad: {customer_data['days_since_last_activity']}
    - Tickets abiertos actualmente: {customer_data['open_tickets']}
    - Total tickets históricos: {customer_data['total_tickets']}
    - Revenue total: ${customer_data['total_revenue']:,.2f}
    - Oportunidades ganadas: {customer_data['opportunities_won']}
    - Oportunidades perdidas: {customer_data['opportunities_lost']}
    - Engagement de email: {customer_data['email_engagement']}
    
    Proporciona:
    1. Health Score (0-100) - siendo 100 salud perfecta
    2. Churn Risk (low/medium/high)
    3. Exactamente 3 acciones recomendadas específicas y accionables
    4. Un breve análisis (2-3 oraciones) del estado actual del cliente
    
    IMPORTANTE: Responde SOLO con JSON válido en este formato exacto:
    {{
        "health_score": 75,
        "churn_risk": "medium",
        "analysis": "Breve análisis aquí del estado del cliente",
        "recommendations": [
            "Primera acción específica y accionable",
            "Segunda acción específica y accionable",
            "Tercera acción específica y accionable"
        ]
    }}
    """
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        ai_analysis = json.loads(response_text)
        
        return ai_analysis
    
    except Exception as e:
        st.error(f"Error en análisis AI: {str(e)}")
        return None

def main():
    st.title("🎯 AI Customer Health Monitor")
    st.markdown("**Análisis automático de salud de clientes usando Claude AI**")
    st.markdown("---")
    
    try:
        df = pd.read_csv('customers_data.csv')
    except FileNotFoundError:
        st.error("❌ No se encontró el archivo customers_data.csv")
        st.stop()
    
    tab1, tab2 = st.tabs(["📊 Análisis Individual", "📈 Dashboard General"])
    
    with tab1:
        st.subheader("Selecciona un cliente para analizar")
        
        customer_names = df['name'].tolist()
        selected_customer_name = st.selectbox(
            "Cliente:",
            options=customer_names,
            index=0
        )
        
        customer_data = df[df['name'] == selected_customer_name].iloc[0].to_dict()
        
        st.markdown("### 📋 Datos del Cliente")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Días sin actividad", customer_data['days_since_last_activity'])
            st.metric("Revenue Total", f"${customer_data['total_revenue']:,.0f}")
        
        with col2:
            st.metric("Tickets Abiertos", customer_data['open_tickets'])
            st.metric("Total Tickets", customer_data['total_tickets'])
        
        with col3:
            st.metric("Oport. Ganadas", customer_data['opportunities_won'])
            st.metric("Oport. Perdidas", customer_data['opportunities_lost'])
        
        with col4:
            engagement_emoji = {
                'high': '🟢',
                'medium': '🟡',
                'low': '🟠',
                'very_low': '🔴'
            }
            st.metric(
                "Email Engagement", 
                f"{engagement_emoji.get(customer_data['email_engagement'], '⚪')} {customer_data['email_engagement']}"
            )
        
        st.markdown("---")
        
        if st.button("🤖 Analizar con Claude AI", type="primary", use_container_width=True):
            
            with st.spinner("🤖 Analizando con Claude AI..."):
                ai_result = analyze_customer_with_ai(customer_data)
            
            if ai_result:
                st.markdown("### 🎯 Análisis de IA")
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=ai_result['health_score'],
                        title={'text': "Health Score", 'font': {'size': 24}},
                        gauge={
                            'axis': {'range': [None, 100], 'tickwidth': 1},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 33], 'color': "lightcoral"},
                                {'range': [33, 66], 'color': "lightyellow"},
                                {'range': [66, 100], 'color': "lightgreen"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 50
                            }
                        }
                    ))
                    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    risk_color = {
                        'low': '🟢 BAJO',
                        'medium': '🟡 MEDIO',
                        'high': '🔴 ALTO'
                    }
                    risk_label = risk_color.get(ai_result['churn_risk'], '⚪ DESCONOCIDO')
                    st.markdown(f"### Riesgo de Churn: {risk_label}")
                
                with col2:
                    st.markdown("#### 📝 Análisis:")
                    st.info(ai_result['analysis'])
                    
                    st.markdown("#### 💡 Recomendaciones:")
                    for i, rec in enumerate(ai_result['recommendations'], 1):
                        st.markdown(f"**{i}.** {rec}")
                
                with st.expander("🔍 Ver respuesta completa de la IA"):
                    st.json(ai_result)
    
    with tab2:
        st.subheader("Análisis masivo de clientes")
        
        num_customers = st.slider(
            "¿Cuántos clientes analizar?",
            min_value=3,
            max_value=len(df),
            value=min(5, len(df)),
            help="Cada análisis consume créditos de API"
        )
        
        if st.button("🚀 Analizar clientes seleccionados", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            
            for idx in range(num_customers):
                customer_data = df.iloc[idx].to_dict()
                status_text.text(f"Analizando {customer_data['name']}... ({idx+1}/{num_customers})")
                
                ai_result = analyze_customer_with_ai(customer_data)
                
                if ai_result:
                    results.append({
                        'Cliente': customer_data['name'],
                        'Health Score': ai_result['health_score'],
                        'Riesgo': ai_result['churn_risk'],
                        'Revenue': customer_data['total_revenue'],
                        'Días sin actividad': customer_data['days_since_last_activity'],
                        'Tickets abiertos': customer_data['open_tickets']
                    })
                
                progress_bar.progress((idx + 1) / num_customers)
            
            status_text.text("✅ ¡Análisis completado!")
            
            results_df = pd.DataFrame(results)
            
            st.markdown("### 📊 Métricas Globales")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_health = results_df['Health Score'].mean()
                st.metric("Health Score Promedio", f"{avg_health:.0f}/100")
            
            with col2:
                high_risk = len(results_df[results_df['Riesgo'] == 'high'])
                st.metric("Clientes Alto Riesgo", high_risk, delta=f"{(high_risk/len(results_df)*100):.0f}%")
            
            with col3:
                total_revenue = results_df['Revenue'].sum()
                st.metric("Revenue Total", f"${total_revenue:,.0f}")
            
            with col4:
                at_risk_revenue = results_df[results_df['Riesgo'] == 'high']['Revenue'].sum()
                st.metric("Revenue en Riesgo", f"${at_risk_revenue:,.0f}")
            
            st.markdown("---")
            
            st.markdown("### 📋 Resultados Detallados")
            st.dataframe(
                results_df.style.background_gradient(subset=['Health Score'], cmap='RdYlGn'),
                use_container_width=True,
                height=400
            )
            
            st.markdown("### 📊 Health Scores por Cliente")
            fig = px.bar(
                results_df.sort_values('Health Score'),
                x='Health Score',
                y='Cliente',
                color='Riesgo',
                color_discrete_map={
                    'low': '#90EE90',
                    'medium': '#FFD700',
                    'high': '#FF6B6B'
                },
                orientation='h',
                text='Health Score'
            )
            fig.update_traces(texttemplate='%{text}', textposition='outside')
            fig.update_layout(height=400, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
    