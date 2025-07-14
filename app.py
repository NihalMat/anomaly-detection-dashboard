# 📊 Plotly Dash App for LATAM Payment Anomaly Monitoring (Interactive)

import dash
from dash import html, dcc, Output, Input
import pandas as pd
import plotly.graph_objects as go

# Load datasets
latam_df = pd.read_csv("latam_failure_pct.csv", parse_dates=['date'])
ml_df = pd.read_csv("latam_ml_anomaly.csv", parse_dates=['date'])
arima_df = pd.read_csv("arima_forecast.csv", parse_dates=['date'])

# App setup
app = dash.Dash(__name__)
app.title = "LATAM Payment Monitoring"

# Layout
app.layout = html.Div([
    html.H1("📉 LATAM Payment Failure Anomaly Dashboard"),

    html.Div([
        html.Label("Select Forecast Overlay:"),
        dcc.Dropdown(
            options=[
                {'label': 'ARIMA Forecast', 'value': 'arima'},
                {'label': 'None', 'value': 'none'}
            ],
            value='arima',
            id='forecast-selector'
        ),

        html.Label("Anomaly Detection Method:"),
        dcc.RadioItems(
            options=[
                {'label': 'None', 'value': 'none'},
                {'label': 'ML-Based (Isolation Forest)', 'value': 'ml'}
            ],
            value='ml',
            id='anomaly-toggle',
            labelStyle={'display': 'inline-block', 'marginRight': '15px'}
        ),

        html.Label("Simulate Black Friday Spike:"),
        dcc.Checklist(
            options=[{'label': 'Enable Spike (Jan 25–28)', 'value': 'bf'}],
            value=[],
            id='event-toggle'
        ),

        html.Label("Select Date Range:"),
        dcc.DatePickerRange(
            id='date-picker',
            min_date_allowed=latam_df['date'].min(),
            max_date_allowed=latam_df['date'].max(),
            start_date=latam_df['date'].min(),
            end_date=latam_df['date'].max()
        )
    ], style={'width': '70%', 'marginBottom': '20px'}),

    dcc.Graph(id='failure-graph'),

    html.Div(id='impact-summary', style={'marginTop': '30px', 'borderTop': '1px solid #ccc', 'paddingTop': '20px'})
])

# Callback for interactivity
@app.callback(
    Output('failure-graph', 'figure'),
    Output('impact-summary', 'children'),
    Input('forecast-selector', 'value'),
    Input('anomaly-toggle', 'value'),
    Input('event-toggle', 'value'),
    Input('date-picker', 'start_date'),
    Input('date-picker', 'end_date')
)
def update_graph(forecast_choice, anomaly_method, event_toggle, start_date, end_date):
    # Slice base data
    df = latam_df.copy()
    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    # Apply Black Friday spike
    if 'bf' in event_toggle:
        spike_mask = (df['date'] >= '2025-01-25') & (df['date'] <= '2025-01-28')
        df.loc[spike_mask, 'failure_pct'] *= 2.5

    # Build figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['failure_pct'],
        mode='lines+markers', name='Failure %', line=dict(color='gray')
    ))

    if anomaly_method == 'ml':
        ml_anomalies = ml_df[(ml_df['ml_anomaly']) & (ml_df['date'] >= start_date) & (ml_df['date'] <= end_date)]
        fig.add_trace(go.Scatter(
            x=ml_anomalies['date'], y=ml_anomalies['failure_pct'],
            mode='markers', name='ML Anomalies', marker=dict(color='red', size=10, symbol='x')
        ))

    if forecast_choice == 'arima':
        arima_overlay = arima_df[(arima_df['date'] >= start_date) & (arima_df['date'] <= end_date)]
        fig.add_trace(go.Scatter(
            x=arima_overlay['date'], y=arima_overlay['forecast'],
            mode='lines', name='ARIMA Forecast', line=dict(color='green', dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=arima_overlay['date'], y=arima_overlay['upper'], line=dict(width=0), showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=arima_overlay['date'], y=arima_overlay['lower'], fill='tonexty', fillcolor='rgba(0,200,0,0.1)',
            line=dict(width=0), name='Forecast CI', showlegend=True
        ))

    fig.update_layout(
        title="📈 LATAM Payment Failures with Forecast & Anomalies",
        xaxis_title="Date",
        yaxis_title="Failure %",
        template="plotly_white",
        hovermode="x unified"
    )

    # Simulated product impact summary
    failure_days = df[df['failure_pct'] > 3]
    user_count = len(df)
    fail_count = len(failure_days)
    fail_pct = (fail_count / user_count) * 100 if user_count > 0 else 0

    summary = html.Div([
        html.H4("📊 User & Business Impact Summary (Simulated):"),
        html.P(f"• Date Range: {start_date} to {end_date}"),
        html.P(f"• Total Records: {user_count}"),
        html.P(f"• High Failure Days (>3%): {fail_count} ({fail_pct:.1f}%)"),
        html.P(f"• Simulated Missed Revenue: ${fail_count * 5700:,}"),
        html.P("• Root cause: Deployment A41 + Gateway v3-latam-02 (injected)" if 'bf' not in event_toggle else "• Spike simulated due to Black Friday")
    ])

    return fig, summary

# Run server
if __name__ == '__main__':
    app.run_server(debug=True)
