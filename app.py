from dash import Dash, html, dcc, callback, Output, Input, State
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash.dependencies import Output, Input
import cv2
import base64
import numpy as np
from flask import Flask, Response

data = [
    {
        "Timestamp": f"2024-11-19 12:{i:02d}:00",
        "Image File": f"image_{i}.jpg",
        "Detections": f"{i} crack(s)",
        "Location": f"Lat: {14.6 + i * 0.01:.4f}, Lon: {120.9 + i * 0.01:.4f}"
    }
    for i in range(10)  # Create 10 rows
]

table_body = [
    html.Tr(
        [
            html.Td(row["Timestamp"]),
            html.Td(row["Image File"]),
            html.Td(row["Detections"]),
            html.Td(row["Location"])
        ]
    )
    for row in data
]

url = 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png'
attribution = '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> '

server = Flask(__name__)
app = Dash(
    __name__,
    server=server,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
        "https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/css/bootstrap.min.css",
        "//fonts.googleapis.com/css?family=Roboto|Lato",
    ])
app.title = "Rail Crack Detection"
app.css.config.serve_locally = True

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)

    def __del__(self):
        self.video.release()

    def get_frame(self):
        success, image = self.video.read()
        image = cv2.resize(image, (550, 390))
        #image = cv2.rectangle(image, (150,150), (300,380), (255,0,0), 2)
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@server.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()), mimetype='multipart/x-mixed-replace; boundary=frame')


app.layout = [
    html.Div(
        [
        html.Div(
            [
            html.Div([
                html.Img(
                    src=app.get_asset_url('hamburger.png'),
                    style={"width":"32px","height":"32px"},
                    id='open-fs',
                    n_clicks=0),
                html.H1('Rail Crack Detection'),
                ],className='top-bar'
            ),
            html.Div(
                [
                    html.Div(
                        html.Img(src='/video_feed',style={"height":"550", "width":"390"}), #/video_feed
                        #html.Div('Live Feed',style={"height":"100%", "width":"90%","backgroundImage":"url('https://www.bworldonline.com/wp-content/uploads/2021/10/railway.jpg')","backgroundSize":"cover","border":"1px #292828 solid"}),
                        className='live-feed-panel'
                    ),
                    html.Div(
                        [
                            html.P("Cracks Detected: 21"),
                            dbc.Button("Capture",id='capture-fs')
                        ],className='feed-control'
                    )
                ],className='left-panel'
            )
            ], className='main-panel'
        ),
        dl.Map(
            [dl.TileLayer(), dl.Marker(position=[14.621565284493693, 121.05015539180206])],
            center=[14.621565284493693, 121.05015539180206], 
            zoom=22,
            className='map-panel'
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Menu")),
                dbc.ModalBody(
                    html.Div(
                        [
                            html.Div(id='map-button'),
                            html.Div(id='data-button'),
                            html.Div(id='email-button')
                        ],className='menu-panel'
                    )
                ),
            ],id="menu-modal",
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Crack Detection Confirmation")),
                dbc.ModalBody(
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.P('Timestamp: 2024-11-20T18:46:23'),
                                    html.P('Cracks Detected: 44'),
                                    html.P('GPS Coordinates: Lat 55, Long 14')
                                ],style={'flexGrow':'1'}
                            ),
                            html.Div(
                                'Lat 55, Long 14',
                                style={
                                    'flexGrow':'3',
                                    "backgroundImage":"url('https://www.bworldonline.com/wp-content/uploads/2021/10/railway.jpg')",
                                    "backgroundSize":"cover",
                                    "border":"1px #292828 solid",
                                    "height":'100%'
                                }
                            )
                        ],style={
                            'display':'flex',
                            'height':'100%'     
                        }
                    )
                ),
                dbc.ModalFooter(
                    html.Div(
                        [
                            dbc.Button("Confirm", id="confirm-capture", className="ms-auto", n_clicks=0),
                            dbc.Button("Cancel", id="confirm-cancel", className="ms-auto", n_clicks=0, style={'backgroundColor':'red','border':'red'})
                        ],style={'display':'flex','justifyContent':'end','gap':'16px'}
                    )
                ),
            ],id='capture-modal'
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Crack Detection Map")),
                dbc.ModalBody(
                    dl.Map(
                        [dl.TileLayer(), dl.Marker(position=[14.621565284493693, 121.05015539180206])],
                        center=[14.621565284493693, 121.05015539180206], 
                        zoom=22,
                        style={'height':'100%','width':'100%'}
                    )
                )
            ],id='map-modal'
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Crack Logs")),
                dbc.ModalBody(
                    dbc.Table(
                        [
                            html.Thead(
                                html.Tr(
                                    [
                                        html.Th("Timestamp"),
                                        html.Th("Image File"),
                                        html.Th("Detections"),
                                        html.Th("Location")
                                    ])
                                )
                        ] + table_body, 
                        bordered=True,  
                        dark=True
                    ), style={'overflowY':'scroll'}
                )
            ],id='logs-modal'
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Send Data via Email")),
                dbc.ModalBody(
                    html.Div(
                        [
                        html.Label("Send to:"),
                        dbc.Input(
                            id="email-input",
                            type="email",
                            placeholder="example@example.com",
                            style={"width": "80%"},
                        ),
                        dbc.Button("Send", id="send-button", color="primary"),
                        ],style={'display':'flex','gap':'16px','alignItems':'center'}
                    )
                )
            ],id='send-modal'
        )
        ],
        className='whole-panel'
    )
]

@app.callback(
    Output("menu-modal", "is_open"),
    Input("open-fs", "n_clicks"),
    State("menu-modal", "is_open"),
)
def toggle_modal(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("capture-modal", "is_open"),
    Input("capture-fs", "n_clicks"),
    Input("confirm-capture", "n_clicks"),
    Input("confirm-cancel", "n_clicks"),
    State("capture-modal", "is_open"),
)
def toggle_modal(n,confirm,cancel, is_open):
    if n or cancel or confirm:
        return not is_open
    return is_open

@app.callback(
    Output("map-modal", "is_open"),
    Input("map-button", "n_clicks"),
    State("map-modal", "is_open"),
)
def toggle_modal(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("logs-modal", "is_open"),
    Input("data-button", "n_clicks"),
    State("logs-modal", "is_open"),
)
def toggle_modal(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("send-modal", "is_open"),
    Input("email-button", "n_clicks"),
    State("send-modal", "is_open"),
)
def toggle_modal(n, is_open):
    if n:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port="8050", debug=True)
