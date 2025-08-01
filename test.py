import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd

# Dane główne – kategorie
main_data = pd.DataFrame({
    "Kategoria": ["Informatyka", "Matematyka", "Fizyka", "Chemia"],
    "Ilość": [120, 80, 60, 40],
    "x": [1, 2, 3, 4],  # pozycje na osi x (umieszczone blisko siebie)
    "y": [1, 1, 1, 1]  # wszystkie na tej samej wysokości
})
# Tekst: nazwa kategorii oraz ilość
main_data["Tekst"] = main_data["Kategoria"] + " (" + main_data["Ilość"].astype(str) + ")"

# Podkategorie – dla każdej głównej kategorii
subcategories = {
    "Informatyka": pd.DataFrame({
        "Podkategoria": ["Programowanie", "Sieci", "Algorytmy"],
        "Ilość": [70, 30, 20],
        "x": [1, 2, 3],
        "y": [1, 1, 1]
    }),
    "Matematyka": pd.DataFrame({
        "Podkategoria": ["Algebra", "Geometria", "Statystyka"],
        "Ilość": [40, 30, 10],
        "x": [1, 2, 3],
        "y": [1, 1, 1]
    }),
    "Fizyka": pd.DataFrame({
        "Podkategoria": ["Mechanika", "Elektrodynamika", "Termodynamika"],
        "Ilość": [30, 20, 10],
        "x": [1, 2, 3],
        "y": [1, 1, 1]
    }),
    "Chemia": pd.DataFrame({
        "Podkategoria": ["Organiczna", "Nieorganiczna", "Analityczna"],
        "Ilość": [15, 15, 10],
        "x": [1, 2, 3],
        "y": [1, 1, 1]
    })
}


# Funkcja tworząca wykres głównych kategorii
def create_main_chart():
    fig = px.scatter(
        main_data, x="x", y="y",
        size="Ilość", text="Tekst",
        size_max=100
    )
    fig.update_traces(textposition='middle center')
    fig.update_layout(
        title="Główne kategorie (kliknij na bąbelek)",
        clickmode='event+select',
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig


# Funkcja tworząca wykres podkategorii dla wybranej kategorii
def create_subcategory_chart(category):
    df_sub = subcategories.get(category)
    if df_sub is None:
        return create_main_chart()
    df_sub["Tekst"] = df_sub["Podkategoria"] + " (" + df_sub["Ilość"].astype(str) + ")"
    fig = px.scatter(
        df_sub, x="x", y="y",
        size="Ilość", text="Tekst",
        size_max=100
    )
    fig.update_traces(textposition='middle center')
    fig.update_layout(
        title=f"Podkategorie: {category} (kliknij, aby wrócić)",
        clickmode='event+select',
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig


# Inicjalizacja aplikacji Dash
app = dash.Dash(__name__)
app.layout = html.Div([
    dcc.Graph(id='bubble-chart', figure=create_main_chart()),
    # Ukryty div do przechowywania aktualnej kategorii (widoku)
    html.Div(id='current-category', style={'display': 'none'})
])


# Callback reagujący na kliknięcie bąbelka
@app.callback(
    Output('bubble-chart', 'figure'),
    Output('current-category', 'children'),
    Input('bubble-chart', 'clickData'),
    State('current-category', 'children')
)
def update_chart(clickData, current_category):
    ctx = dash.callback_context
    if not ctx.triggered or clickData is None:
        return create_main_chart(), ""

    clicked_text = clickData['points'][0]['text']

    if current_category:
        # Jeśli jesteśmy w widoku podkategorii – kliknięcie powoduje powrót do widoku głównego
        return create_main_chart(), ""
    else:
        # W widoku głównym – kliknięcie na bąbelek powoduje przejście do podkategorii
        category = clicked_text.split(" (")[0]
        if category in subcategories:
            return create_subcategory_chart(category), category
    return create_main_chart(), ""


if __name__ == '__main__':
    app.run_server(debug=True)
