#####################################################################
#                                                                   #
# /naqs_devices/KeysightXSeries/labscript_devices.py                #
#                                                                   #
# Copyright 2018, David Meyer                                       #
#                                                                   #
# This file is part of the naqslab devices extension to the         #
# labscript_suite. It is licensed under the Simplified BSD License. #
#                                                                   #
#                                                                   #
#####################################################################
import numpy as np

# from naqs_devices import ScopeChannel, CounterScopeChannel
from labscript import Device, TriggerableDevice, config, LabscriptError, set_passed_properties

__version__ = '0.5.0'
__author__ = ['dihm']      
              
import labscript_devices

##############################################
# define helper sub-classes of labscript defined channels

from labscript import Device, AnalogIn, StaticDDS, LabscriptError


class ScopeChannel(AnalogIn):
    """Subclass of labscript.AnalogIn that marks an acquiring scope channel.
    """
    description = 'Scope Acquisition Channel Class'

    def __init__(self, name, parent_device, connection):
        """This instantiates a scope channel to acquire during a buffered shot.

        Args:
            name (str): Name to assign channel
            parent_device (obj): Handle to parent device
            connection (str): Which physical scope channel is acquiring.
                              Generally of the form \'Channel n\' where n is
                              the channel label.
        """
        Device.__init__(self,name,parent_device,connection)
        self.acquisitions = []

    def acquire(self):
        """Inform BLACS to save data from this channel.

        Note that the parent_device controls when the acquisition trigger is sent.
        """
        if self.acquisitions:
            raise LabscriptError('Scope Channel {0:s}:{1:s} can only have one acquisition!'.format(self.parent_device.name,self.name))
        else:
            self.acquisitions.append({'label': self.name})


class CounterScopeChannel(ScopeChannel):
    """Subclass of :obj:`ScopeChannel` that allows for pulse counting."""
    description = 'Scope Acquisition Channel Class with Pulse Counting'

    def __init__(self, name, parent_device, connection):
        """This instantiates a counter scope channel to acquire during a buffered shot.

        Args:
            name (str): Name to assign channel
            parent_device (obj): Handle to parent device
            connection (str): Which physical scope channel is acquiring.
                              Generally of the form \'Channel n\' where n is
                              the channel label.
        """
        ScopeChannel.__init__(self,name,parent_device,connection)
        self.counts = []

    def count(self,typ,pol):
        """Register a pulse counter operation for this channel.

        Args:
            typ (str): count 'pulse' or 'edge'
            pol (str): reference to 'pos' or 'neg' edges
        """
        # guess we can allow multiple types of counters per channel
        if (typ in ['pulse', 'edge']) and (pol in ['pos', 'neg']):
            self.counts.append({'type':typ,'polarity':pol})
        else:
            raise LabscriptError('Invalid counting parameters for {0:s}:{1:s}'.format(self.parent_name,self.name)) 


# class StaticFreqAmp(StaticDDS):
#     """A Static Frequency that supports frequency and amplitude control.

#     If phase control is needed, use labscript.StaticDDS"""
#     description = 'Frequency Source class for Signal Generators'

#     def __init__(self, *args, **kwargs):
#         """This instantiates a static frequency output channel.

#         Frequency and amplitude limits set here will supersede those dictated
#         by the device class, but only when compiling a shot with runmanager.
#         Static update limits are enforced by the BLACS Tab for the parent device.

#         Args:
#             *args: Passed to parent init.
#             **kwargs: Passed to parent init.

#         Raises:
#             LabscriptError: If **kwargs contains phase settings, which are not supported.
#         """

#         if not {'phase_limits','phase_conv_class','phase_conv_params'}.isdisjoint(kwargs.keys()):
#             raise LabscriptError(f'{self.device.name} does not support any phase configurations.')

#         super().__init__(*args,**kwargs)
#         # set default values within limits specified
#         # if not specified, use limits from parent device
#         try:
#             parent_device = kwargs['parent_device']
#         except KeyError:
#             parent_device = args[1]
#         freq_limits = kwargs.get('freq_limits')
#         amp_limits = kwargs.get('amp_limits')
#         if freq_limits is not None:
#             self.frequency.default_value = freq_limits[0]
#         else:
#             self.frequency.default_value = parent_device.freq_limits[0]/parent_device.scale_factor
#         if amp_limits is not None:
#             self.amplitude.default_value = amp_limits[0]
#         else:
#             self.amplitude.default_value = parent_device.amp_limits[0]/parent_device.amp_scale_factor

#     def setphase(self,value,units=None):
#         """Overridden from StaticDDS so as not to provide phase control, which
#         is generally not supported by :obj:`SignalGenerator` devices.
#         """
#         raise LabscriptError('StaticFreqAmp does not support phase control')
        
class KeysightXScope(TriggerableDevice):
    description = 'Keysight X Series Digital Oscilliscope'
    allowed_children = [ScopeChannel]
    
    @set_passed_properties(property_names = {
        "device_properties":["VISA_name",
                            "compression","compression_opts","shuffle"]}
        )
    def __init__(self, name, VISA_name, trigger_device, trigger_connection, 
        num_AI=4, DI=True, trigger_duration=1e-3,
        compression=None, compression_opts=None, shuffle=False, **kwargs):
        '''VISA_name can be full VISA connection string or NI-MAX alias.
        Trigger Device should be fast clocked device. 
        num_AI sets number of analog input channels, default 4
        DI sets if DI are present, default True
        trigger_duration set scope trigger duration, default 1ms
        Compression of traces in h5 file controlled by:
        compression: \'lzf\', \'gzip\', None 
        compression_opts: 0-9 for gzip
        shuffle: True/False '''
        self.VISA_name = VISA_name
        self.BLACS_connection = VISA_name
        TriggerableDevice.__init__(self,name,trigger_device,trigger_connection,**kwargs)
        
        self.compression = compression
        if (compression == 'gzip') and (compression_opts == None):
            # set default compression level if needed
            self.compression_opts = 4
        else:
            self.compression_opts = compression_opts
        self.shuffle = shuffle
        
        self.trigger_duration = trigger_duration
        self.allowed_analog_chan = ['Channel {0:d}'.format(i) for i in range(1,num_AI+1)]
        if DI:
            self.allowed_pod1_chan = ['Digital {0:d}'.format(i) for i in range(0,8)]
            self.allowed_pod2_chan = ['Digital {0:d}'.format(i) for i in range(8,16)]        
        
    def generate_code(self, hdf5_file):
        '''Automatically called by compiler to write acquisition instructions
        to h5 file. Configures counters, analog and digital acquisitions.'''    
        Device.generate_code(self, hdf5_file)
        trans = {'pulse':'PUL','edge':'EDG','pos':'P','neg':'N'}
        
        acqs = {'ANALOG':[],'POD1':[],'POD2':[]}
        for channel in self.child_devices:
            if channel.acquisitions:
                # make sure channel is allowed
                if channel.connection in self.allowed_analog_chan:
                    acqs['ANALOG'].append((channel.connection,channel.acquisitions[0]['label']))
                elif channel.connection in self.allowed_pod1_chan:
                    acqs['POD1'].append((channel.connection,channel.acquisitions[0]['label']))
                elif channel.connection in self.allowed_pod2_chan:
                    acqs['POD2'].append((channel.connection,channel.acquisitions[0]['label']))
                else:
                    raise LabscriptError('{0:s} is not a valid channel.'.format(channel.connection))
        
        acquisition_table_dtypes = np.dtype({'names':['connection','label'],'formats':['a256','a256']})
        
        grp = self.init_device_group(hdf5_file)
        # write tables if non-empty to h5_file                        
        for acq_group, acq_chan in acqs.items():
            if len(acq_chan):
                table = np.empty(len(acq_chan),dtype=acquisition_table_dtypes)
                for i, acq in enumerate(acq_chan):
                    table[i] = acq
                grp.create_dataset(acq_group+'_ACQUISITIONS',compression=config.compression,
                                    data=table)
                grp[acq_group+'_ACQUISITIONS'].attrs['trigger_time'] = self.trigger_time
                                    
        # now do the counters
        counts = []
        for channel in self.child_devices:
            if hasattr(channel, 'counts'):
                for counter in channel.counts:
                    counts.append((channel.connection,
                                    trans[counter['type']],
                                    trans[counter['polarity']]))
        counts_table_dtypes = np.dtype({'names':['connection','type','polarity'],'formats':['a256','a256','a256']})
        counts_table = np.empty(len(counts),dtype=counts_table_dtypes)
        for i,count in enumerate(counts):
            counts_table[i] = count
        if len(counts_table):
            grp.create_dataset('COUNTERS',compression=config.compression,data=counts_table)
            grp['COUNTERS'].attrs['trigger_time'] = self.trigger_time
                                
    def acquire(self,start_time):
        '''Call to define time when trigger will happen for scope.'''
        if not self.child_devices:
            raise LabscriptError('No channels acquiring for trigger {0:s}'.format(self.name))
        else:
            self.parent_device.trigger(start_time,self.trigger_duration)
            self.trigger_time = start_time
