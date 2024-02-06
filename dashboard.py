import dash                                                    
from dash import html, dcc, Input, Output, State, dash_table
import pandas as pd                                             
import plotly.express as px
import pymongo                                                  
from bson.objectid import ObjectId

client = pymongo.MongoClient(
    "mongodb+srv://user:test@test-bed.dtgmi5a.mongodb.net/?retryWrites=true&w=majority")

db = client["zoo-emo"]
collection = db["users"]

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                suppress_callback_exceptions=True)

app.layout = html.Div([
    html.H1('Test Dashboard', style={'textAlign': 'center'}),
    dcc.Interval(id='interval_db', interval=86400000 * 7, n_intervals=0),
    html.Div(id='mongo-datatable', children=[]),
    dcc.Store(id='changed-cell'),
    dcc.Graph(id='gender-pie-chart', className='five columns'),
    dcc.Graph(id='age-bar-chart', className='five columns'),
    dcc.Graph(id='age-enrollment-scatter', className='five columns')
])


@app.callback(Output('mongo-datatable', component_property='children'),
              Input('interval_db', component_property='n_intervals'))
def populate_datatable(n_intervals):
    df = pd.DataFrame(list(collection.find()))
    df['_id'] = df['_id'].astype(str)
    print(df.head(20))

    return [
        dash_table.DataTable(
            id='our-table',
            data=df.to_dict('records'),
            columns=[{'id': p, 'name': p, 'editable': False} if p == '_id'
                     else {'id': p, 'name': p, 'editable': True}
                     for p in df],
        ),
    ]


@app.callback(Output('gender-pie-chart', 'figure'),
              Input('interval_db', 'n_intervals'))
def update_pie_chart(n_intervals):
    df = pd.DataFrame(list(collection.find()))
    gender_counts = df['gender'].value_counts()
    fig = px.pie(values=gender_counts, names=gender_counts.index, title='Gender Percentage')
    return fig


@app.callback(Output('age-bar-chart', 'figure'),
              Input('interval_db', 'n_intervals'))
def update_age_bar_chart(n_intervals):
    df = pd.DataFrame(list(collection.find()))
    fig = px.histogram(df, x='age', title='Age Distribution')
    return fig


@app.callback(Output('age-enrollment-scatter', 'figure'),
              Input('interval_db', 'n_intervals'))
def update_age_enrollment_scatter(n_intervals):
    df = pd.DataFrame(list(collection.find()))
    df['enrolledDate'] = pd.to_datetime(df['enrolledDate'])
    df['enrollment_length'] = (pd.to_datetime('now') - df['enrolledDate']).dt.days
    fig = px.scatter(df, x='age', y='enrollment_length', title='Age vs Enrollment Length')
    return fig


app.clientside_callback(
    """
    function (input,oldinput) {
        if (oldinput != null) {
            if(JSON.stringify(input) != JSON.stringify(oldinput)) {
                for (i in Object.keys(input)) {
                    newArray = Object.values(input[i])
                    oldArray = Object.values(oldinput[i])
                    if (JSON.stringify(newArray) != JSON.stringify(oldArray)) {
                        entNew = Object.entries(input[i])
                        entOld = Object.entries(oldinput[i])
                        for (const j in entNew) {
                            if (entNew[j][1] != entOld[j][1]) {
                                changeRef = [i, entNew[j][0]] 
                                break        
                            }
                        }
                    }
                }
            }
            return changeRef
        }
    }    
    """,
    Output('changed-cell', 'data'),
    Input('our-table', 'data'),
    State('our-table', 'data_previous')
)


if __name__ == '__main__':
    app.run_server(debug=False)
