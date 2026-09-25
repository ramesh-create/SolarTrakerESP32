import QtQuick
import QtQuick3D

Item {
    id: root
    property real markerLat: 50.187
    property real markerLon: 8.739
    property real lonOffset: 0
    property real zoomFaktor: 1.0
    property real viewYaw: 8.739
    property real viewPitch: 50.187
    property string ortName: ""
    property string ortZeit: ""
    signal ortGeklickt(real lat, real lon)

    readonly property real kugelRadius: 100
    readonly property real grundAbstand: 320
    readonly property real fov: 40

    function abstand() { return grundAbstand / zoomFaktor }
    function kameraPosition() {
        var la = viewPitch * Math.PI / 180.0
        var lo = viewYaw * Math.PI / 180.0
        return Qt.vector3d(abstand() * Math.cos(la) * Math.sin(lo),
                           abstand() * Math.sin(la),
                           abstand() * Math.cos(la) * Math.cos(lo))
    }
    function posAufKugel(lat, lon) {
        var la = lat * Math.PI / 180.0
        var lo = (lon + lonOffset) * Math.PI / 180.0
        return Qt.vector3d(kugelRadius * Math.cos(la) * Math.sin(lo),
                           kugelRadius * Math.sin(la),
                           kugelRadius * Math.cos(la) * Math.cos(lo))
    }
    function zeigeStandort() {
        viewYaw = markerLon + lonOffset
        viewPitch = Math.max(-89, Math.min(89, markerLat))
    }
    function resetAnsicht() {
        zoomFaktor = 1.0
        zeigeStandort()
    }
    // Klickpunkt (Bildschirm) -> Ort auf der Kugel, ohne pick.
    function punktAusMaus(mx, my) {
        var w = view.width, h = view.height
        if (w < 1 || h < 1) return null
        var la = viewPitch * Math.PI / 180.0
        var lo = viewYaw * Math.PI / 180.0
        var d = abstand()
        var c = Qt.vector3d(d * Math.cos(la) * Math.sin(lo), d * Math.sin(la), d * Math.cos(la) * Math.cos(lo))
        var f = c.times(-1).normalized()
        var weltOben = Qt.vector3d(0, 1, 0)
        var r = f.crossProduct(weltOben).normalized()
        if (r.length() < 0.0001) r = Qt.vector3d(1, 0, 0)
        var u = r.crossProduct(f).normalized()
        var aspect = w / h
        var th = Math.tan(fov * Math.PI / 180.0 / 2.0)
        var ndcx = (mx - w / 2) / (w / 2)
        var ndcy = -(my - h / 2) / (h / 2)
        var dir = f.plus(r.times(ndcx * th * aspect)).plus(u.times(ndcy * th)).normalized()
        var b = c.dotProduct(dir)
        var cc = c.dotProduct(c) - kugelRadius * kugelRadius
        var disc = b * b - cc
        if (disc < 0) return null
        var t = -b - Math.sqrt(disc)
        var p = c.plus(dir.times(t))
        var lat = Math.asin(Math.max(-1, Math.min(1, p.y / kugelRadius))) * 180.0 / Math.PI
        var lon = Math.atan2(p.x, p.z) * 180.0 / Math.PI - lonOffset
        while (lon > 180) lon -= 360
        while (lon < -180) lon += 360
        return Qt.vector2d(lat, lon)
    }

    onMarkerLatChanged: zeigeStandort()
    onMarkerLonChanged: zeigeStandort()
    Component.onCompleted: zeigeStandort()

    View3D {
        id: view
        anchors.fill: parent
        camera: kamera
        environment: SceneEnvironment {
            clearColor: "#0d1117"
            backgroundMode: SceneEnvironment.Color
        }

        PerspectiveCamera {
            id: kamera
            position: root.kameraPosition()
            fieldOfView: root.fov
            onPositionChanged: lookAt(Qt.vector3d(0, 0, 0))
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

    MouseArea {
        anchors.fill: parent
        property real pressX: 0
        property real pressY: 0
        property real startYaw: 0
        property real startPitch: 0
        onPressed: function (mouse) {
            pressX = mouse.x; pressY = mouse.y
            startYaw = root.viewYaw; startPitch = root.viewPitch
        }
        onPositionChanged: function (mouse) {
            if (!pressed)
                return
            root.viewYaw = startYaw - (mouse.x - pressX) * 0.35
            root.viewPitch = Math.max(-89, Math.min(89, startPitch + (mouse.y - pressY) * 0.35))
        }
        onDoubleClicked: function (mouse) {
            var p = root.punktAusMaus(mouse.x, mouse.y)
            if (p)
                root.ortGeklickt(p.x, p.y)
        }
        onWheel: function (wheel) {
            var f = Math.pow(1.0016, wheel.angleDelta.y)
            root.zoomFaktor = Math.max(0.5, Math.min(3.2, root.zoomFaktor * f))
            wheel.accepted = true
        }
    }

    Column {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.margins: 10
        spacing: 2
        Text { text: "Breite: " + root.markerLat.toFixed(3) + "\u00B0"; color: "#3aa6ff"; font.pixelSize: 13 }
        Text { text: "Laenge: " + root.markerLon.toFixed(3) + "\u00B0"; color: "#3aa6ff"; font.pixelSize: 13 }
        Text { text: "Ortszeit: " + root.ortZeit; color: "#97a8bb"; font.pixelSize: 12 }
        Text { text: "Ziehen = drehen, Rad = Zoom, Doppelklick = Standort"; color: "#697b8e"; font.pixelSize: 11 }
    }

    Text {
        id: markerLabel
        text: root.ortName
        color: "#ffffff"
        font.bold: true
        font.pixelSize: 13
        // Marker auf der Rueckseite ausblenden
        visible: text !== "" && (function () {
            var P = root.posAufKugel(root.markerLat, root.markerLon)
            var C = root.kameraPosition()
            return (P.x * C.x + P.y * C.y + P.z * C.z) > 0
        })()
        x: {
            root.viewYaw; root.viewPitch; root.zoomFaktor; view.width; view.height
            var p = view.mapFrom3DScene(root.posAufKugel(root.markerLat, root.markerLon))
            return Math.max(2, Math.min(view.width - width - 2, p.x + 10))
        }
        y: {
            root.viewYaw; root.viewPitch; root.zoomFaktor; view.width; view.height
            var p = view.mapFrom3DScene(root.posAufKugel(root.markerLat, root.markerLon))
            return Math.max(2, Math.min(view.height - height - 2, p.y - 8))
        }
    }
}
