from dash import Dash, html, dcc, callback, Output, Input, State
import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash.dependencies import Output, Input
from flask import Response, Flask, send_file, make_response
import os
from datetime import datetime
import requests
import time

from support_funcs import getCurentLoc, get_local_wlan_address, generate_qr_code
from crud import getAllCoordinates, insertDetection, getAllDetections, deleteByID, export_to_csv


PORT ="8050"

data = {'location':[14.621565284493693,121.05015539180206]}
app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
        "https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/css/bootstrap.min.css",
        "//fonts.googleapis.com/css?family=Roboto|Lato",
        "https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css"
    ])
app.title = "Rail Crack Detection"
app.css.config.serve_locally = True
server = app.server


@server.route("/download-files")
def download_files():
    export_to_csv()
    return send_file('download/rail_cracks.zip', as_attachment=True, mimetype="application/zip")


#App Layout Components
def updateMap(id='',className=''):
    device_location = getCurentLoc()

    warning_icon = dict(
        iconUrl=app.get_asset_url('warning.png'),
        iconSize=[40, 40],
        iconAnchor=[40, 40]
    )
    accept_icon = dict(
        iconUrl=app.get_asset_url('accept.png'),
        iconSize=[30, 30],
        iconAnchor=[30, 30]
    )
    cracks_location = [
        dl.Marker(id={"type": "marker", "index": f"Null"},position=[1,1])
        
    ]+[
        dl.Marker(
            id={"type": "marker", "index": f"{id}_{x["id"]}"},
            position=x['locations'],
            icon=warning_icon
        ) 
        if x['has_detections'] else 
        dl.Marker(
            id={"type": "marker", "index": f"{id}_{x["id"]}"},
            position=x['locations'],
            icon=accept_icon
        ) 
        for x in getAllCoordinates()
    ]

    if id=='map-whole':
        zoom=15
    else:
        zoom=22

    return dl.Map(
        [
            dl.TileLayer(url = 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png'), 
            dl.Marker(position=device_location,title='Current Location')
        ] + cracks_location,
        id=id,  
        center=data['location'], 
        zoom=zoom,
        className=className
    )

topbarPanel = html.Div(
    [
        html.Img(
            src=app.get_asset_url('hamburger.png'),
            style={"width":"32px","height":"32px"},
            id='open-fs',
            n_clicks=0),
        html.H1('Rail Crack Detection'),
    ],
    className='top-bar'
)

camfeedPanel = html.Div(
    [
        html.Div(
            html.Img(
                src='http://127.0.0.1:5000/video_feed',
                style={"height":"480", "width":"640"},
                id='cam_feed'
            ),
            className='live-feed-panel'
        ),
        html.Div(
            dbc.Button("Capture",id='capture-fs'),
            className='feed-control'
        )
    ],
    className='left-panel'
)

menuModal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Menu")),
        dbc.ModalBody(
            html.Div(
                [
                    html.Div(id='map-button'),
                    html.Div(id='data-button'),
                    html.Div(id='email-button')
                ],
                className='menu-panel'
            )
        )
    ],
    content_class_name='modal-large',
    id="menu-modal",
)

captureModal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Crack Detection Confirmation"),close_button=False),
        dbc.ModalBody(
            html.Div(
                [
                    html.Div(
                        '',
                        style={'flexGrow':'1'},
                        id='confirm-panel'
                    ),
                    html.Div(
                        html.Img(id='confirm-image',style={"width":"400px","height":"300px"}),
                        style={
                            'width':'420px',
                            'display':'flex',
                            'alignItems':'center',
                            'justifyContent':'center'
                        }
                    )
                ],
                style={'display':'flex'}
            )
        ),
        dbc.ModalFooter(
            html.Div(
                [
                    dbc.Button(
                        "Save",
                        id="confirm-capture",
                        className="ms-auto",
                        color='success',
                        n_clicks=0
                    ),
                    dbc.Button(
                        "Cancel",
                        id="confirm-cancel",
                        className="ms-auto",
                        n_clicks=0,
                        color='danger'
                    )
                ],
                style={'display':'flex','justifyContent':'end','gap':'16px'}
            )
        ),
    ],
    content_class_name='modal-large',
    enforceFocus=True,
    keyboard=False,
    backdrop='static',
    id='capture-modal'
)

mapModal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Crack Detection Map")),
        dbc.ModalBody(
            '',
            id='map-modal-whole-panel',
            className='map-modal-whole'
        )
    ],
    content_class_name='modal-large',
    id='map-modal'
)

logsModal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Crack Logs")),
        dbc.ModalBody(style={'overflowY':'scroll'}, id='logs-table')
    ],
    content_class_name='modal-large',
    id='logs-modal'
)

sendModal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Download Data")),
        dbc.ModalBody(
            html.Div(
                [
                    html.P("Ensure receiving device is within local network."),
                    html.Img(
                        src=generate_qr_code(f'http://{get_local_wlan_address()}:{PORT}/download-files'), 
                        id="qr-code", 
                        style={"height":'350px',"width":'350px'}
                    )
                ],style={'display':'flex','flexDirection':'column','justifyContent':'center','alignItems':'center'}
            )
        )
    ],
    content_class_name='modal-large',
    id='send-modal'
)

viewModal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("View Record")),
        dbc.ModalBody(
            html.Div(
                [
                    html.Div([
                        dbc.Table(
                            [
                                html.Thead(html.Tr([html.Th("Field"), html.Th("Value")])),
                                html.Tbody(
                                    [
                                        html.Tr([html.Td('ID'),html.Td(id='record-id')]),
                                        html.Tr([html.Td('Timestamp'),html.Td(id='record-timestamp')]),
                                        html.Tr([html.Td('Detections'),html.Td(id='record-detections')]),
                                        html.Tr([html.Td('Location'),html.Td(id='record-location')]),
                                        html.Tr([html.Td('Filename'),html.Td(id='record-filename')])
                                    ]
                                )
                            ],
                            bordered=True,  
                            dark=True,
                        )
                    ]
                    ,style={'flexGrow':'1','padding':'8px'}),
                    html.Div([
                        html.Img(
                            src="",
                            style={"width":"400px","height":"300px"},
                            id='record-image'
                        )
                    ],style={'flexGrow':'1','display':'flex','alignItems':'center','justifyContent':'center'})
                ],style={
                    'display':'flex',
                    'width':'100%'
                }
            )
        ),
        dbc.ModalFooter(
            html.Div(
                [
                    dbc.Button(
                        "Delete",
                        id="delete-fs",
                        className="ms-auto",
                        n_clicks=0,
                        color='danger'
                    )
                ],
                style={'display':'flex','justifyContent':'end','gap':'16px'}
            )
        ),
    ],
    content_class_name='modal-large',
    enforceFocus=True,
    id='view-modal'
)

deleteModal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Delete Record")),
        dbc.ModalBody(
            [
                html.P(
                    "Are you sure you want to delete this record?",
                    style={'textAlign':'center','marginTop':'32px','marginBottom':'32px'}                       
                ),
                html.Div(
                    [
                        dbc.Button("Cancel",id='delete-cancel', color="secondary"),
                        dbc.Button("Confirm",id='delete-confirm',color='danger')
                    ],
                    style={'display':'flex','justifyContent':'end','gap':'16px'}
                )
            ]
        )
    ],
    content_class_name='modal-mini',
    enforceFocus=True,
    keyboard=False,
    backdrop='static',
    size="sm",
    id='delete-modal'
)

#Main Layout
app.layout = [html.Div(
    [
        html.Div(
            [
                topbarPanel,
                camfeedPanel
            ], 
            className='main-panel'
        ),
        html.Div(
            '',
            className='map-panel',
            id='map-home-panel'
        ),
        menuModal,
        captureModal,
        mapModal,
        logsModal,
        sendModal,
        viewModal,
        deleteModal,
        dcc.Location(id="loc-url"),
        dcc.Store(id='store-record')
    ],
    className='whole-panel'
)]



#Menu Modal Callback
@app.callback(
    Output("menu-modal", "is_open"),
    Input("open-fs", "n_clicks"),
    State("menu-modal", "is_open"),
)
def toggle_menu_modal(n, is_open):
    if n:
        return not is_open
    return is_open



#Delete Modal Callback
@app.callback(
    Output("delete-modal", "is_open"),
    Input("delete-fs", "n_clicks"),
    Input("delete-cancel", "n_clicks"),
    Input("delete-confirm", "n_clicks"),
    State("delete-modal", "is_open"),
    State("record-id",'children'),
    prevent_initial_callback=True
)
def toggle_delete_modal(n, cancel, confirm, is_open, id):
    if confirm and is_open:
        deleteByID(id)

    if n or cancel:
        return not is_open
    return is_open



def confirmPanelChildren(data):
    if data is None:
        return []
    
    loc = data['location']
    print(f"Timestamp: {data['timestamp']}, Filename: {data['filename']}, Location: {loc}")
    
    sleepers, cracks, popouts = None, None, None
    if data['detections'].get('Sleeper'):
        sleepers = f"{data['detections'].get('Sleeper')} Sleeper(s)"
    if data['detections'].get('Crack'):
        cracks = f"{data['detections'].get('Crack')} Crack(s)"
    if data['detections'].get('Popout'):
        popouts = f"{data['detections'].get('Popout')} Popout(s)"

    if sleepers is None and cracks is None and popouts is None:
        style={'display':'block'}
    else:
        style={'display':'None'}

    return [
        html.P(f'Timestamp: {datetime.strptime(data['timestamp'], "%Y%m%d %H%M%S")}',style={'marginBottom':'0'},id='confirm-timestamp'),
        html.P('Detections:',style={'marginBottom':'4px'}),
        html.P(sleepers,style={'marginBottom':'2px'},id='sleepers-desc'),
        html.P(cracks,style={'marginBottom':'2px'},id='cracks-desc'),
        html.P(popouts,style={'marginBottom':'2px'},id='popouts-desc'),
        html.P("No cracks detected",style=style),
        html.P(f'GPS: {round(loc[0],4)} Lat, {round(loc[1],4)} Long',style={'marginBottom':'0'},id='confirm-gps'),
        dl.Map(
            [dl.TileLayer(
                url = 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png'
            ),dl.Marker(position=loc)],
            center = list(loc) ,
            zoom=20,
            style={'height':'175px','marginTop':'4px'},
            id='confirm-map'
        ),
    ]



#Confirm Modal Callback
@app.callback(
    Output("capture-modal", "is_open"),
    Output("confirm-panel","children"),
    Output("confirm-image",'src'),
    Input("capture-fs", "n_clicks"),
    Input("confirm-capture", "n_clicks"),
    Input("confirm-cancel", "n_clicks"),
    State("capture-modal", "is_open"),
    prevent_initial_call = True
)
def toggle_confirm_modal(n, confirm, cancel, is_open):
    global data
    if cancel and is_open:
        os.remove(data['filename'])
        return not is_open, [], ''
    
    if confirm and is_open:
        insertDetection(
            timestamp=datetime.strptime(data['timestamp'],"%Y%m%d %H%M%S"),
            image_file=data['filename'],
            detections=data['detections'],
            location=data['location']
        )
        return not is_open, [], ''
    
    if n and not is_open:
        try:
            print('Capturing Image')
            response = requests.post("http://127.0.0.1:5000/capture")
            if response.status_code == 200:
                data = response.json()
                data.update({'location':getCurentLoc()})
                panel = confirmPanelChildren(data)
                return not is_open, panel, app.get_asset_url(data['filename'].strip('assets/'))
            
            else:
                print(f"Failed to capture image. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                return not is_open, [], ''
            
        except requests.exceptions.RequestException as e:
            print(f"Error occurred: {e}")
            return not is_open, [], ''
    else:
        return not is_open, [], ''



#Update Maps Callback
@app.callback(
    Output('map-home-panel',"children"),
    Output('map-modal-whole-panel',"children"),
    Input("confirm-capture", "n_clicks"),
    Input("delete-confirm", "n_clicks")
)
def update_map_call(confirm,delete):
    print('Updating Maps')
    return updateMap(id='map-home',className='map-panel'), updateMap(id='map-whole',className='map-modal-whole')



#Map Modal Callback
@app.callback(
    Output("map-modal", "is_open"),
    Input("map-button", "n_clicks"),
    State("map-modal", "is_open"),
)
def toggle_map_modal(n, is_open):
    if n:
        return not is_open
    return is_open




def format_detections(detections):
    return ", ".join([f"{k}: {v}" for k, v in detections.items()])



#Logs Modal Callback
@app.callback(
    Output("logs-modal", "is_open"),
    Output("logs-table","children"),
    Input("data-button", "n_clicks"),
    State("logs-modal", "is_open"),
)
def toggle_logs_modal(n, is_open):

    table_header = [
        html.Thead(html.Tr([
            html.Th("Timestamp"), 
            html.Th("Image File"), 
            html.Th("Detections"), 
            html.Th("Location")
        ]))
    ]
    rows = [
        html.Tr([
            html.Td(str(i["timestamp"])),
            html.Td(i['image_file']),
            html.Td(format_detections(i["detections"])),
            html.Td(str(i['locations']))
        ])
        for i in getAllDetections()
    ]

    table_body = [html.Tbody(rows)]
    table = dbc.Table(
                table_header+table_body,
                bordered=True,  
                dark=True,
            ),

    if n:
        return not is_open, table
    return is_open, table



#Send Modal Callback
@app.callback(
    Output("send-modal", "is_open"),
    Input("email-button", "n_clicks"),
    State("send-modal", "is_open"),
)
def toggle_send_modal(n, is_open):
    if n:
        return not is_open
    return is_open



#View Modal Callback
@app.callback(
    Output("view-modal", "is_open"),
    Output("record-id", "children"),
    Output("record-timestamp", "children"),
    Output("record-detections", "children"),
    Output("record-location", "children"),
    Output("record-filename", "children"),
    Output("record-image", "src"),
    Input({"type": "marker", "index": dash.ALL}, "n_clicks"),
    Input("delete-confirm", "n_clicks"),
    Input('confirm-capture', "n_clicks"),
    State("view-modal", "is_open"),
    State("capture-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_view_modal(n_clicks, delete_confirm, confirm_capture, is_open, capture_is_open):
    if delete_confirm and is_open:
        return not is_open, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    else:
        if confirm_capture and capture_is_open:
            return is_open, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
        else:
            marker_id = ctx.triggered[0]["prop_id"]
            marker_id = marker_id.split(".")[0]
            if eval(marker_id)['index']=='Null':
                return is_open, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
            else:
                marker_index = eval(marker_id)["index"].split("_")[1]
                record = next((rec for rec in getAllDetections() if str(rec["_id"]) == marker_index), None)

                if record:
                    return not is_open \
                        ,str(record['_id']) \
                        ,str(record['timestamp']) \
                        ,[f'{k}: {v} 'for k, v in record['detections'].items()] \
                        ,f'{record['locations'][0]} , {record['locations'][1]}' \
                        ,record['image_file'].strip('assets/db/') \
                        ,app.get_asset_url(record['image_file'].strip('assets/'))
                
            return is_open, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=PORT, debug=False)
