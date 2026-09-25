import QtQuick
import QtQuick3D

Item {
    id: root
    property real markerLat: 50.187
    property real markerLon: 8.739
    property real lonOffset: 0
    property real zoomFaktor: 1.0
    property string ortName: ""
    property string ortZeit: ""
    signal ortGeklickt(real lat, real lon)

    property real kugelRadius: 100

    function posAufKugel(lat, lon) {
        var la = lat * Math.PI / 180.0;
        var lo = (lon + lonOffset) * Math.PI / 180.0;
        return Qt.vector3d(kugelRadius * Math.cos(la) * Math.sin(lo),
                           kugelRadius * Math.sin(la),
                           kugelRadius * Math.cos(la) * Math.cos(lo));
    }

    function zeigeStandort() {
        gestell.eulerRotation.y = markerLon + lonOffset
        gestell.eulerRotation.x = -markerLat
    }

    onMarkerLatChanged: zeigeStandort()
    onMarkerLonChanged: zeigeStandort()
    Component.onCompleted: zeigeStandort()

    View3D {
        id: view
        anchors.fill: parent
        environment: SceneEnvironment {
            clearColor: "#0d1117"
            backgroundMode: SceneEnvironment.Color
        }

        // Kamera auf einem drehbaren Gestell -> Globus bleibt in Weltkoordinaten.
        Node {
            id: gestell
            eulerRotation.y: 8.739
            eulerRotation.x: -50.187
            PerspectiveCamera {
                id: kamera
                position: Qt.vector3d(0, 0, 320 / root.zoomFaktor)
                fieldOfView: 40
            }
        }
        DirectionalLight { eulerRotation.x: -30; brightness: 1.1 }
        DirectionalLight { eulerRotation.y: 150; brightness: 0.5 }

        Node {
            id: globus
            Model {
                source: "#Sphere"
                scale: Qt.vector3d(root.kugelRadius / 50, root.kugelRadius / 50, root.kugelRadius / 50)
                materials: PrincipledMaterial {
                    baseColorMap: Texture { source: "weltkarte.png" }
                    lighting: PrincipledMaterial.NoLighting
                }
            }
            Model {
                source: "#Sphere"
                scale: Qt.vector3d(root.kugelRadius * 1.004 / 50, root.kugelRadius * 1.004 / 50, root.kugelRadius * 1.004 / 50)
                materials: PrincipledMaterial {
                    baseColorMap: Texture { source: "gitter.png" }
                    alphaMode: PrincipledMaterial.Blend
                    lighting: PrincipledMaterial.NoLighting
                }
            }
            Model {
                id: marker
                source: "#Sphere"
                scale: Qt.vector3d(3.4 / 50, 3.4 / 50, 3.4 / 50)
                position: root.posAufKugel(root.markerLat, root.markerLon)
                materials: PrincipledMaterial {
                    baseColor: "#ff5252"
                    lighting: PrincipledMaterial.NoLighting
                }
            }
        }
    }

    DragHandler {
        target: null
        property real startY: 0
        property real startX: 0
        onActiveChanged: if (active) { startY = gestell.eulerRotation.y; startX = gestell.eulerRotation.x }
        onTranslationChanged: {
            gestell.eulerRotation.y = startY + translation.x * 0.35
            gestell.eulerRotation.x = Math.max(-89, Math.min(89, startX + translation.y * 0.35))
        }
    }

    WheelHandler {
        onWheel: function (event) {
            var f = Math.pow(1.0016, event.angleDelta.y)
            root.zoomFaktor = Math.max(0.5, Math.min(3.2, root.zoomFaktor * f))
        }
    }

    TapHandler {
        onDoubleTapped: function (eventPoint) {
            var r = view.pick(eventPoint.position.x, eventPoint.position.y)
            if (r.objectHit) {
                var p = r.position
                var len = Math.sqrt(p.x*p.x + p.y*p.y + p.z*p.z)
                if (len < 1)
                    return
                var lat = Math.asin(p.y / len) * 180.0 / Math.PI
                var lon = Math.atan2(p.x, p.z) * 180.0 / Math.PI - root.lonOffset
                while (lon > 180) lon -= 360
                while (lon < -180) lon += 360
                root.ortGeklickt(lat, lon)
            }
        }
    }

    Column {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.margins: 10
        spacing: 2
        Text { text: root.ortName; color: "#e7edf5"; font.bold: true; font.pixelSize: 14 }
        Text { text: "Breite: " + root.markerLat.toFixed(3) + "\u00B0"; color: "#3aa6ff"; font.pixelSize: 13 }
        Text { text: "Laenge: " + root.markerLon.toFixed(3) + "\u00B0"; color: "#3aa6ff"; font.pixelSize: 13 }
        Text { text: "Ortszeit: " + root.ortZeit; color: "#97a8bb"; font.pixelSize: 12 }
        Text { text: "Ziehen = drehen, Rad = Zoom, Doppelklick = Standort"; color: "#697b8e"; font.pixelSize: 11 }
    }
}
