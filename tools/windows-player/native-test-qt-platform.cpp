/* Register the existing static SDK platform used by the upstream GUI test.
 * The selected CSD model test defaults to offscreen and creates no window.
 */
#ifdef HAVE_CONFIG_H
#include "config.h"
#endif
#include <QtPlugin>
Q_IMPORT_PLUGIN(QOffscreenIntegrationPlugin)
