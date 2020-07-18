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
import numpy as np
import webbrowser
from threading import Timer
import copy

pd.set_option('precision', 2)
graph = {}
logdf = pd.DataFrame()
all_teams_df = pd.DataFrame()
start_time = end_time = ''
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

def open_browser():
      webbrowser.open_new('http://127.0.0.1:1000/')

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'EDGE Dashboard'
server = app.server
# team_names = ['Pressure','Filter Status','Gas flow speed','Oxygen top','Oxygen 1','Oxygen 2',
#                 'Gas Temp','Platform','Build Chamber','Optical Bench','Collimator','Pump1',
#             'Pump','Cabinet','Cabinet 2','Ambiance']
team_names = []
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
    dcc.Store(id='store', data=time.time()),
    ])]),
    ]),
    html.Div(id='tabs-example-content')
])

def parse_contents(contents, filename, date):
    global all_teams_df, logdf, start_time, end_time, team_names
    _, content_string = contents.split(',')

    # decoded = base64.b32encode(content_string)
    # decoded = base64.b32decode(content_string)
    decoded = base64.b64decode(content_string)
    print('POSITION -1')
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = create_table(io.StringIO(decoded.decode('utf-8')))
            print('POSITION 5')
            # df = create_table(io.StringIO(content_string))
            all_teams_df = df
            team_names = list(all_teams_df.columns.values)
            team_names.remove('Seconds')
        elif 'log' in filename:
            # Assume that the user uploaded a LOG file
            df= pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep='^([^ ]+ +[^ ]+) +(.*)$', names=['useless','Time','Desc'], 
                index_col=False, engine='python')
            df.drop('useless' , axis = 1)
            df['Time'] =  pd.to_datetime(df['Time'], format='%Y/%m/%d %H:%M:%S,%f')
            start_time = df[df['Desc'].str.contains('Start Build Job', regex=False)]['Time'].values[0]
            end_time = df[df['Desc'].str.contains('build job finished', regex=False)]['Time'].values[0]
            logdf = df
            if not all_teams_df.empty: #if df is full
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
    df = df.query('@end_time> index > @start_time')
    df['Seconds'] = np.arange(len(df))
    all_teams_df = df
    start_time = end_time = ''

def create_table(filename=None):
    # global start_time,end_time
    # log_file = True

    # if start_time=='' or end_time=='':
    #     log_file = False   

    # df = pd.read_csv((filename), sep = ";", usecols=lambda x: x in ['Time','Pressure','Filter Status','Gas flow speed','Oxygen top','Oxygen 1','Oxygen 2',
    #                                                                 'Gas Temp','Platform','Build Chamber','Optical Bench','Collimator','Pump1',
    #                                                                 'Pump','Cabinet','Cabinet 2','Ambiance'])
    # try:
    #     df['Time'] =  pd.to_datetime(df['Time'], format='%a %b %d %H:%M:%S %Y')
    # except:
    #     df['Time'] =  pd.to_datetime(df['Time'], format='%m/%d/%y %H:%M:%S')

    # if log_file:
    #     df = df.query('@end_time> Time > @start_time')
    #     start_time = end_time = ''

    # df['Seconds'] = np.arange(len(df))
    # print(df.dtypes)
    # df = df.set_index('Time')
    # df = df.resample('30S').mean()

    # return df
    print('POSITION 0')
    global start_time,end_time
    var = ['Pressure','Filter Status','Gas flow speed','Oxygen top','Oxygen 1','Oxygen 2',
    'Gas Temp','Platform','Build Chamber','Optical Bench','Collimator','Pump1',
    'Pump','Cabinet','Cabinet 2','Ambiance']
    filename_2 = copy.deepcopy(filename)
    log_file = True

    if start_time=='' or end_time=='':
        log_file = False

    print('POSITION 1')

    df = pd.read_csv((filename), sep = ";", usecols=lambda x: x in var, dtype={c: np.float32 for c in var})
    print('POSITION 2')
    time = pd.read_csv(filename_2, sep = ";", usecols=['Time'],squeeze=True)
    print('POSITION 3')
    try:
        df['Time'] =  pd.to_datetime(time, format='%a %b %d %H:%M:%S %Y')
    except:
        df['Time'] =  pd.to_datetime(time, format='%m/%d/%y %H:%M:%S')

    if log_file:
        df = df.query('@end_time> Time > @start_time')
        start_time = end_time = ''
    df['Seconds'] = np.arange(len(df))
    print(df.dtypes)
    df = df.set_index('Time')
    df = df.resample('30S').mean()
    print('POSITION 4')
    return df

@app.callback(
    [Output('group-select', 'value'),
    Output('group-select', 'options')],
    [Input('output-data-upload', 'children')]
)
def update_options(contents):
    global all_teams_df, team_names
    team_names = list(all_teams_df.columns.values)
    k = [{'label': i, 'value': i} for i in team_names]
    return ['Pressure'], k

@app.callback(
    [Output('sensor-data-graph', 'figure'),
     Output('store', 'data'),],
    [Input('group-select', 'value'),
     Input('output-data-upload', 'children')],
    [State('store', 'data'),
     State('upload-data', 'filename')]
)
def update_graph(grpname, contents, t, uploadedfile):
    global graph

    print('graph func called')
    print(grpname)

    if uploadedfile is None:
        print('sorry u havent uploaded any file')
        return dash.no_update, dash.no_update

    elif contents is None:
        print('not fully loaded')
        return dash.no_update, dash.no_update

    elif 'csv' not in uploadedfile[0] and all_teams_df.empty:
        print(uploadedfile)
        print('sorry u havent uploaded any csv file')
        return dash.no_update, dash.no_update

    elif len(grpname) >= 1:
        row=col=1
        if len(grpname) > 1:
        
            fig = make_subplots(rows=(len(grpname)//2 + len(grpname)%2), cols=2,  horizontal_spacing = 0.015 , vertical_spacing = 0.05, subplot_titles=grpname)
            for x in grpname:
                # memoisation
                # if x in graph:
                #     fig.add_trace(graph[x],row=row, col=col)
                #     print(x,' called from graph')
                # else:
                #     graph[x] = go.Scattergl(x=all_teams_df.index,y=all_teams_df[x], name=x)
                #     fig.add_trace(graph[x],row=row, col=col)
                #     print('Added to graph: ',x)

                fig.add_trace(go.Scattergl(x=all_teams_df.index,y=all_teams_df[x], name=x),row=row, col=col)
                if col == 2:
                    row += 1
                    col = 0
                col += 1
        else:
            fig = go.Figure(data=go.Scattergl(x=all_teams_df.index, y=all_teams_df[grpname[0]]))
            fig.update_layout(title = grpname[0])
    
        fig.update_layout(showlegend=False)
    else:
        fig = go.Figure(data=go.Scattergl(x=all_teams_df.index, y=all_teams_df['Pressure']))
        print(grpname)
        fig.update_layout(title = grpname[0])
        fig.update_layout(showlegend=False)
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
    # Timer(1, open_browser).start()
    app.run_server(port='1000')
