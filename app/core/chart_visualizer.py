# app/core/chart_visualizer.py
# Genera graficos interactivos de velas con Plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_candlestick_chart(df, symbol: str = "BTCUSDT", annotations_list=None):
    """
    Devuelve un go.Figure con velas, EMA 20, Bollinger Bands, Volumen y RSI.
    """
    import pandas_ta as ta
    if "EMA_20"     not in df.columns: df.ta.ema(length=20,   append=True)
    if "RSI_14"     not in df.columns: df.ta.rsi(length=14,   append=True)
    if "BBL_20_2.0" not in df.columns: df.ta.bbands(length=20, std=2, append=True)

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2],
        subplot_titles=(f"{symbol} - Precio & Bollinger", "Volumen", "RSI 14"),
    )

    # Velas
    fig.add_trace(go.Candlestick(
        x=df["open_time"], open=df["open"], high=df["high"],
        low=df["low"],     close=df["close"], name="Precio"
    ), row=1, col=1)

    # EMA 20
    if "EMA_20" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["open_time"], y=df["EMA_20"], mode="lines",
            name="EMA 20", line=dict(color="cyan", width=2)
        ), row=1, col=1)

    # Bollinger
    if "BBU_20_2.0" in df.columns and "BBL_20_2.0" in df.columns:
        fig.add_trace(go.Scatter(x=df["open_time"], y=df["BBU_20_2.0"], mode="lines",
            line=dict(width=0), showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["open_time"], y=df["BBL_20_2.0"], mode="lines",
            name="Bollinger", fill="tonexty", fillcolor="rgba(255,255,255,0.08)",
            line=dict(width=0)), row=1, col=1)

    # Volumen
    colores = ["green" if df["close"].iloc[i] >= df["open"].iloc[i] else "red" for i in range(len(df))]
    fig.add_trace(go.Bar(x=df["open_time"], y=df["volume"], name="Vol",
                         marker_color=colores), row=2, col=1)

    # RSI
    if "RSI_14" in df.columns:
        fig.add_trace(go.Scatter(x=df["open_time"], y=df["RSI_14"], mode="lines",
            name="RSI", line=dict(color="violet", width=2)), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red",   row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="lime",  row=3, col=1)

    fig.update_layout(
        template="plotly_dark", height=800,
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
    )
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)
    return fig
