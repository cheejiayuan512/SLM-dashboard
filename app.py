import base64
import io
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_table
import time
import pandas as pd
import datetime as dt

logdf = all_teams_df = pd.DataFrame()
start_time = end_time = ''
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'EDGE Dashboard'
server = app.server
team_names = ['Pressure','Filter Status','Gas flow speed','Gas pump power','Oxygen top','Oxygen 2','Gas Temp','Platform','Build Chamber','Optical Bench',
'Collimator']
app.layout = html.Div([
    dcc.Tabs(id='tabs-example', value='tab-1', children=[
        dcc.Tab(label='Upload CSV/XLS data', value='tab-1',children=[html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '98%',
            'height': '20%',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'marginTop': '10px', 
            'margin': 'auto'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div(id='output-data-upload'),
])]),
        dcc.Tab(label='Charts', value='tab-2', children=[html.Div([
    html.Div([dcc.Checklist(id='group-select', options=[{'label': i, 'value': i} for i in team_names],
                            style={'width': '100%'},value=['Pressure'], labelStyle={'display': 'inline-block'})]),
     html.Div(id='graph-div'),
    dcc.Graph(id='sensor-data-graph', 
              config={'displayModeBar': False , 'displaylogo': False},
              style={'height': 1000}),
    dcc.Store(id='store', data=time.time())])]),
    ]),
    html.Div(id='tabs-example-content')
])

def parse_contents(contents, filename, date):
    global all_teams_df, logdf, start_time, end_time
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = create_table(io.StringIO(decoded.decode('utf-8')))
            all_teams_df = df
        elif 'log' in filename:
            # Assume that the user uploaded a LOG file
            df= pd.read_csv(io.StringIO(decoded.decode('utf-8')), names=['Time','Desc'], index_col=False)#read strngio into a df
            df[['Microseconds','Desc']] = df['Desc'].str.split(' ', 1, expand=True)#split into time and desc of info with space as delimiter
            df= df.drop(['Microseconds'], axis=1)
            start_time = df[df['Desc'].str.contains('Start Build Job', regex=False)]['Time'].values[0]
            end_time = df[df['Desc'].str.contains('build job finished', regex=False)]['Time'].values[0]
            logdf = df
            if not all_teams_df.empty:
                modify_table()
    except Exception as e:
        return html.Div([
            'There was an error processing file: ',str(filename),' ---- Error: ', str(e)
        ])
    
    return html.Div([
        html.H5(filename),
        html.H6(dt.datetime.fromtimestamp(date)),

        dash_table.DataTable(
            data=df[:100].to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns]
        ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])
# Load Data
def modify_table():
    global all_teams_df,start_time,end_time
    print("hihi i hope no error!")
    df = all_teams_df
    df.drop(columns=["Seconds","Minutes","Minutes and Seconds"])
    df.index = df["Time"]
    df = df[start_time : end_time]
    c = range(len(df.index))
    d = [x//60 for x in c]
    e = [f'{x//60} min {x%60:2d} sec' for x in c]    
    df.insert(0, "Minutes and Seconds", e, True)
    df.insert(0, "Minutes", d, True)
    df.insert(0, "Seconds", c, True)
    df.index = range(len(df.index))
    all_teams_df = df

def create_table(filename=None):
    global start_time,end_time

    log_file = True

    if start_time=='' or end_time=='':
        log_file = False

    if log_file:
        start_time=dt.datetime.strptime(start_time[:19],"%Y/%m/%d %H:%M:%S")
        end_time=dt.datetime.strptime(end_time[:19],"%Y/%m/%d %H:%M:%S")

        print('start_time: ',start_time)
        print('end_time: ',end_time)

    df = pd.read_csv((filename), sep = ";", index_col = 'Time')
    a = list(df.index.values)
    b = []

    try:
        df = df[['Pressure','Filter Status','Gas flow speed','Oxygen top','Oxygen 2',
                'Gas Temp','Platform','Build Chamber','Optical Bench','Collimator',
                'Pump','Cabinet','Cabinet 2','Ambiance']]
        for x in a:
            y = x[4:]
            date_time_obj = dt.datetime.strptime(y, '%b %d %H:%M:%S %Y')
            b += [date_time_obj]
    except KeyError:
        df = df[['Pressure','Filter Status','Gas flow speed','Oxygen 1','Oxygen 2',
                'Gas Temp','Platform','Build Chamber','Optical Bench','Collimator',
                'Pump1','Cabinet','Cabinet 2','Ambiance']]
        for y in a:
            date_time_obj = dt.datetime.strptime(y, '%m/%d/%y %H:%M:%S')
            b+= [date_time_obj]
    df.insert(0, "Time", b, True)
    df.index = b
    
    if log_file:
        df = df[start_time : end_time]
    
    c = range(len(df.index))
    d = [x//60 for x in c]
    e = [f'{x//60} min {x%60:2d} sec' for x in c]    
    df.insert(0, "Minutes and Seconds", e, True)
    df.insert(0, "Minutes", d, True)
    df.insert(0, "Seconds", c, True)
    
    df.index = range(len(df.index))
    
    return df

@app.callback(
    [Output('sensor-data-graph', 'figure'),
     Output('store', 'data')],
    [Input('group-select', 'value'),
     Input('output-data-upload', 'children')],
    [State('store', 'data'),
     State('upload-data', 'filename')]
)
def update_graph(grpname, contents, t, uploadedfile):
    print('graph func called')
    if uploadedfile is None:
        print('sorry u havent uploaded any file')
        return dash.no_update, dash.no_update

    elif contents is None:
        print('not fully loaded')
        return dash.no_update, dash.no_update

    elif  'csv' not in uploadedfile[0] and all_teams_df.empty:
        print(uploadedfile)
        print('sorry u havent uploaded any csv file')
        return dash.no_update, dash.no_update

    elif len(grpname) >= 1:
       row=col=1
       if len(grpname) > 1:
            fig = make_subplots(rows=3, cols=2,  horizontal_spacing = 0.015 , vertical_spacing = 0.03, subplot_titles=grpname)
            for x in grpname:
                fig.add_trace(go.Scattergl(x=all_teams_df['Time'],y=all_teams_df[x], name=x),row=row, col=col)
                if col == 2:
                    row += 1
                    col = 0
                col += 1
       else:
            fig = go.Figure(data=go.Scattergl(x=all_teams_df['Time'], y=all_teams_df[grpname[0]]))
            fig.update_layout(title = grpname[0])
    
       fig.update_layout(showlegend=False)
       fig.update_xaxes(showticklabels=False)
    else:
        fig = go.Figure(data=go.Scattergl(x=all_teams_df['Time'], y=all_teams_df['Pressure']))
        fig.update_layout(title = grpname[0])
        fig.update_layout(showlegend=False)
        fig.update_xaxes(showticklabels=False)
    return fig, time.time()


@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],#returns a list of contents
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [parse_contents(c, n, d) for c, n, d in zip(list_of_contents, list_of_names, list_of_dates)]
        return children


if __name__ == '__main__':
    app.run_server(debug=False ,threaded=True)
