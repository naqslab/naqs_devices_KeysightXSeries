#####################################################################
#                                                                   #
# /naqs_devices/KeysightXSeries/register_classes.py                 #
#                                                                   #
# Copyright 2018, David Meyer                                       #
#                                                                   #
# This file is part of naqs_devices,                                #
# and is licensed under the                                         #
# Simplified BSD License. See the license.txt file in the root of   #
# the project for the full license.                                 #
#                                                                   #
#####################################################################
import labscript_devices

labscript_devices.register_classes(
    'KeysightXScope',
    BLACS_tab='naqs_devices.KeysightXSeries.blacs_tabs.KeysightXScopeTab',
    runviewer_parser='')
