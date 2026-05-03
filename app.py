# новый график
import dash
from dash import dcc, html, Input, Output, State, dash_table, ctx
import pandas as pd
import plotly.express as px
# improve filters
# --- загрузка ---
df = pd.read_csv("data.csv")
df["date"] = pd.to_datetime(df["date"])

colors = {
    "Food": "#636EFA",
    "Transport": "#EF553B",
    "Entertainment": "#00CC96",
    "Salary": "#AB63FA"
}

app = dash.Dash(__name__)

# --- layout ---
app.layout = html.Div([

    html.H1("💸 Финансовый дашборд"),

    # KPI
    html.Div([
        html.Div(id="income"),
        html.Div(id="expense"),
        html.Div(id="balance"),
    ], style={"display": "flex", "gap": "50px", "fontSize": "20px"}),

    html.Hr(),

    # фильтры
    html.Div([
        dcc.Dropdown(df["category"].unique(), id="category", placeholder="Категория"),

        dcc.DatePickerRange(
            id="date-range",
            start_date=df["date"].min(),
            end_date=df["date"].max()
        ),

        html.Button("Сброс", id="reset")
    ], style={"display": "flex", "gap": "20px"}),

    html.Hr(),

    dcc.Graph(id="line"),
    dcc.Graph(id="income-expense"),
    dcc.Graph(id="pie"),
    dcc.Graph(id="top"),
    dcc.Graph(id="hist"),

    html.Hr(),

    html.H3("Добавить запись"),

    html.Div([
        dcc.DatePickerSingle(id="input-date"),
        dcc.Dropdown(df["category"].unique(), id="input-category"),
        dcc.Input(id="input-income", type="number", placeholder="Доход"),
        dcc.Input(id="input-expense", type="number", placeholder="Расход"),
        html.Button("Добавить", id="add"),
        html.Button("Удалить", id="delete"),
    ], style={"display": "flex", "gap": "10px"}),

    dash_table.DataTable(
        id="table",
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict("records"),
        editable=True,
        row_selectable="single",
        page_size=10
    )
])
# add histogram improvements
# --- callback ---
@app.callback(
    Output("line", "figure"),
    Output("income-expense", "figure"),
    Output("pie", "figure"),
    Output("top", "figure"),
    Output("hist", "figure"),
    Output("table", "data"),
    Output("income", "children"),
    Output("expense", "children"),
    Output("balance", "children"),
    Output("category", "value"),
    Output("date-range", "start_date"),
    Output("date-range", "end_date"),

    Input("category", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("add", "n_clicks"),
    Input("delete", "n_clicks"),
    Input("table", "data"),
    Input("reset", "n_clicks"),

    State("table", "selected_rows"),
    State("input-date", "date"),
    State("input-category", "value"),
    State("input-income", "value"),
    State("input-expense", "value"),
)
def update(cat, start, end, add, delete, table_data, reset,
           selected, d, c, i, e):

    global df
    trigger = ctx.triggered_id

    # --- reset ---
    if trigger == "reset":
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, \
               df.to_dict("records"), "", "", "", None, df["date"].min(), df["date"].max()

    # --- редактирование ---
    if trigger == "table":
        df = pd.DataFrame(table_data)
        df["date"] = pd.to_datetime(df["date"])
        df.to_csv("data.csv", index=False)

    # --- добавление ---
    if trigger == "add" and d and c:
        new = pd.DataFrame([{
            "date": pd.to_datetime(d),
            "category": c,
            "income": float(i or 0),
            "expense": float(e or 0)
        }])
        df = pd.concat([df, new], ignore_index=True)
        df.to_csv("data.csv", index=False)

    # --- удаление ---
    if trigger == "delete" and selected:
        df = df.drop(selected).reset_index(drop=True)
        df.to_csv("data.csv", index=False)

    dff = df.copy()

    # --- фильтры ---
    if cat:
        dff = dff[dff["category"] == cat]

    if start and end:
        dff = dff[
            (dff["date"] >= pd.to_datetime(start)) &
            (dff["date"] <= pd.to_datetime(end))
        ]

    if dff.empty:
        return {}, {}, {}, {}, {}, [], "", "", "", cat, start, end

    # --- KPI ---
    inc = dff["income"].sum()
    exp = dff["expense"].sum()

    # --- графики ---
    line = px.line(
        dff.groupby("date", as_index=False)["expense"].sum(),
        x="date",
        y="expense",
        title="Расходы по времени"
    )

    income_expense = px.line(
        dff.groupby("date", as_index=False)[["income", "expense"]].sum(),
        x="date",
        y=["income", "expense"],
        title="Доход vs Расход"
    )

    pie = px.pie(
        dff.groupby("category", as_index=False)["expense"].sum(),
        names="category",
        values="expense",
        color="category",
        color_discrete_map=colors
    )

    top = px.bar(
        dff.groupby("category", as_index=False)["expense"].sum()
           .sort_values("expense", ascending=False),
        x="category",
        y="expense",
        title="Топ категорий"
    )

    hist = px.histogram(dff, x="expense")
# enhance table view
    return (
        line,
        income_expense,
        pie,
        top,
        hist,
        df.to_dict("records"),
        f"Доход: {int(inc)}",
        f"Расход: {int(exp)}",
        f"Баланс: {int(inc-exp)}",
        cat,
        start,
        end
    )

# UI tweaks
if __name__ == "__main__":
    app.run(debug=True)