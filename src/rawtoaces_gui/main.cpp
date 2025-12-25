// SPDX-License-Identifier: Apache-2.0
// Copyright Contributors to the rawtoaces Project.

#include <QGuiApplication>
#include <QWindow>
#include <QDebug>

#include <rhi/qrhi.h>

int main(int argc, char** argv)
{
    QGuiApplication app(argc, argv);

    QWindow window;
    window.resize(640, 480);
    window.setTitle("QRhi 6.10 Test");
    window.show();

#if defined(Q_OS_MACOS)
    QRhiMetalInitParams params;
    QRhi *rhi = QRhi::create(QRhi::Metal, &params);
#else
    QRhi *rhi = QRhi::create(QRhi::Null, nullptr);
#endif

    if (!rhi) {
        qWarning() << "QRhi backend unavailable! Qt likely built without RHI.";
        return 1;
    }

    qInfo() << "QRhi initialized! Backend:" << rhi->backendName();
    delete rhi;
    return 0;
}
