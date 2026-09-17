import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
from glob import glob


# Needed to define data structure
from collections import OrderedDict
from dataclasses import dataclass, InitVar, field
from numbers import Number
import struct
import datetime


ASD_VERSIONS = ['ASD', 'asd', 'as6', 'as7', 'as8']
ASD_HAS_REF = {'ASD': False, 'asd': False, 'as6': True, 'as7': True,
               'as8': True}

ASD_DATA_TYPES = OrderedDict([("RAW_TYPE", "tgt_count"),
                              ("REF_TYPE", "tgt_reflect"),
                              ("RAD_TYPE", "tgt_radiance"),
                              ("NOUNITS_TYPE", None),
                              ("IRRAD_TYPE", "tgt_irradiance"),
                              ("QI_TYPE", None),
                              ("TRANS_TYPE", None),
                              ("UNKNOWN_TYPE", None),
                              ("ABS_TYPE", None)])

ASD_DATA_TYPES_MANUAL = {0:"RAW_TYPE", 1:"REF_TYPE", 2:"RAD_TYPE", 3:"NOUNITS_TYPE", 4:"IRRAD_TYPE", 5:"QI_TYPE",
                         6:"TRANS_TYPE", 7:"UNKNOWN_TYPE", 8:"ABS_TYPE"}

ASD_GPS_DATA = struct.Struct("= 5d 2b cl 2b 5B 2c")

ASD_DATA_FORMAT = {0:"FLOAT_FORMAT", 1:"INTEGER_FORMAT", 2:"DOUBLE_FORMAT",3:"UNKNOWN_FORMAT"}

ASD_INSTRUMENT_TYPE = {0:"UNKNOWN_INSTRUMENT", 1:"PSII_INSTRUMENT", 2:"LSVNIR_INSTRUMENT", 3:"FSVNIR_INSTRUMENT",
                       4:"FSFR_INSTRUMENT", 5:"FSNIR_INSTRUMENT", 6:"CHEM_INSTRUMENT", 7:"FSFR_UNATTENDED_INSTRUMENT",}

# ASD Metadata structre for ASD version 8 first 484 bytes
METADATA_ASD = struct.Struct("< 3s 157s 9h 4c L 1c L 2f 5c H 128s 5d 2b cl 2b 5B 2c L 2h 2H 4f H c 4s 3H c L 4H 2f i 3f h c 2f 5c")



@dataclass
class ASDmetadata:
    """Class for reading and storing asd metadata"""
    # Creo la variable con los datos de foorma interna
    _binconts: InitVar[bytes | None] = None

    product_version : int = field(init=False)
    instrument_manufacturer : str = field(init=False)
    comments : str= field(init=False)
    # date
    time_lock : int = field(init=False)
    second : int = field(init=False)
    minute : int = field(init=False)
    hour : int = field(init=False)
    day : int = field(init=False)
    month : int = field(init=False)
    year : int = field(init=False)
    wday : int = field(init=False)
    yday : int = field(init=False)
    isdst : int = field(init=False)

    measurement_date : str = field(init=False)
    # version
    version : str = field(init=False)
    file_version : str = field(init=False)
    # Dark current
    dc_corr : str = field(init=False)
    dc_time = field(init=False)
    dc_time : str  = field(init=False)
    # Data type
    data_type : str = field(init=False)
    # WR
    wr_time : str = field(init=False)
    wr_time : str = field(init=False)
    # Channels
    ch1_wave : int = field(init=False)
    wave_step : int = field(init=False)
    data_format : str = field(init=False)
    channels : int= field(init=False)
    # GPS info
    gps_true_heading : int = field(init=False)
    gps_speed : int = field(init=False)
    gps_latitude : int = field(init=False)
    gps_longitude : int = field(init=False)
    gps_altitude : int = field(init=False)
    gps_flags : int = field(init=False)
    gps_hardware_mode : int =field(init=False)
    gps_timestamp : int = field(init=False)
    gps_flags2 : int = field(init=False)
    gps_satellites : int = field(init=False)
    gps_filler : int = field(init=False)
    
    # Intrument config
    integration_time : int = field(init=False)
    fore_optics : int = field(init=False)
    dark_current_correction : int = field(init=False)

    calibration_series : int = field(init=False)
    instrument_number : int = field(init=False)

    y_range : tuple = field(init=False)
    x_range : tuple = field(init=False)

    dynamic_range : int = field(init=False)
    xmode : str = field(init=False)

    flags : str = field(init=False)

    dc_count : int = field(init=False)
    wr_count : int = field(init=False)
    sample_count : int = field(init=False)

    instrument_type : str = field(init=False)

    bulb_id : int = field(init=False)

    swir1_gain : int = field(init=False)
    swir2_gain : int = field(init=False)
    swir1_offset : int = field(init=False)
    swir2_offset : int = field(init=False)

    splice1_wavelength : int = field(init=False)
    splice2_wavelength : int = field(init=False)

    
    def __post_init__(self, _binconts):
        _metadata_struct = struct.Struct("< 3s 157s 9h 4c L 1c L 2f 5c H 128s 5d 2b cl 2b 5B 2c L 2h 2H 4f H c 4s 3H c L 4H 2f i 3f h c 2f 5c")
        _metadata_unpacked = _metadata_struct.unpack(_binconts[:484])
        
        # First
        self.product_version : int = _binconts[0:3].decode('utf-8')
        self.instrument_manufacturer : str = _metadata_unpacked[0].decode('utf-8')
        self.comments : str= _metadata_unpacked[1].replace(b'\x00', b'').decode('utf-8')
        # date
        self.time_lock : int = 160
        self.second : int = _metadata_unpacked[2]
        self.minute : int = _metadata_unpacked[3]
        self.hour : int = _metadata_unpacked[4]
        self.day : int = _metadata_unpacked[5]
        self.month : int = _metadata_unpacked[6]
        self.year : int = _metadata_unpacked[7]
        self.wday : int = _metadata_unpacked[8]
        self.yday : int = _metadata_unpacked[9]
        self.isdst : int = _metadata_unpacked[10]
        self.month : int = self.month+1
        self.year : int = self.year+1900
        self.measurement_date : str = f"{self.year:04}-{self.month:02}-{self.day:02} {self.hour:02}:{self.minute:02}:{self.second:02}"
        # version
        self.version : str = _metadata_unpacked[11]
        self.file_version : str = _metadata_unpacked[12]
        # Dark current
        self.dc_corr : str = _metadata_unpacked[14]
        self.dc_time = _metadata_unpacked[15]
        self.dc_time : str  = datetime.datetime.fromtimestamp(self.dc_time).strftime('%Y-%m-%d %H:%M:%S')
        # Data type
        self.data_type : str = ASD_DATA_TYPES_MANUAL[int.from_bytes(_metadata_unpacked[16])]
        # WR
        self.wr_time : str = _metadata_unpacked[17]
        self.wr_time : str = datetime.datetime.fromtimestamp(self.wr_time).strftime('%Y-%m-%d %H:%M:%S')
        # Channels
        self.ch1_wave : int = _metadata_unpacked[18]
        self.wave_step : int = int(_metadata_unpacked[19])
        self.data_format : str = ASD_DATA_FORMAT[int.from_bytes(_metadata_unpacked[20], byteorder='little')]
        self.channels : int= _metadata_unpacked[25]
        # GPS info
        _gps_struct = _metadata_unpacked[27:27+18]
        self.gps_true_heading : int = _gps_struct[0]
        self.gps_speed : int = _gps_struct[1]
        self.gps_latitude : int = _gps_struct[2]
        self.gps_longitude : int = _gps_struct[3]
        self.gps_altitude : int = _gps_struct[4]
        self.gps_flags : int = _gps_struct[5:7] 
        self.gps_hardware_mode : int = _gps_struct[7]
        self.gps_timestamp : int = _gps_struct[8]
        self.gps_flags2 : int = _gps_struct[9:11] # unpack this into bits
        self.gps_satellites : int = _gps_struct[11:16]
        self.gps_filler : int = _gps_struct[16:18]
        
        # Intrument config
        self.integration_time : int = _metadata_unpacked[45]+0.5 if _metadata_unpacked[45] == 8 else _metadata_unpacked[45]
        self.fore_optics : int = _metadata_unpacked[46]
        self.dark_current_correction : int = _metadata_unpacked[47]
    
        self.calibration_series : int = _metadata_unpacked[48]
        self.instrument_number : int = _metadata_unpacked[49]
    
        self.y_range : tuple = (int(_metadata_unpacked[50]), int(_metadata_unpacked[51]))
        self.x_range : tuple = (int(_metadata_unpacked[52]), int(_metadata_unpacked[53]))   
    
        self.dynamic_range : int = _metadata_unpacked[54]
        self.xmode : str = _metadata_unpacked[55]
    
        self.flags : str = _metadata_unpacked[56]
    
        self.dc_count : int = _metadata_unpacked[57]
        self.wr_count : int = _metadata_unpacked[58]
        self.sample_count : int = _metadata_unpacked[59]
    
        self.instrument_type : str = ASD_INSTRUMENT_TYPE[int.from_bytes(_metadata_unpacked[60], byteorder='little')]
    
        self.bulb_id : int = _metadata_unpacked[61]
    
        self.swir1_gain : int = _metadata_unpacked[62]
        self.swir2_gain : int = _metadata_unpacked[63]
        self.swir1_offset : int = _metadata_unpacked[64]
        self.swir2_offset : int = _metadata_unpacked[65]
    
        self.splice1_wavelength : int = _metadata_unpacked[66]
        self.splice2_wavelength : int = _metadata_unpacked[67]

@dataclass
class Spectra(np.lib.mixins.NDArrayOperatorsMixin):
    """Class for keeping track of an item in inventory."""
    name : str
    wave : np.array
    spectrum : np.array
    metadata : ASDmetadata

    def plot(self, **kwargs):
        return plt.plot(self.wave, self.spectrum, **kwargs)
    
    def __array__(self, dtype=None):
        return self.spectrum
        
    def __array_ufunc__(self, ufunc, method, *args, **kwargs):
        values = []
        for value in args:
            if isinstance(value, Number):
                values.append(value)
            elif isinstance(value, Spectra):
                values.append(value.spectrum)
            else:
                return NotImplemented
        return Spectra(name=self.name, wave=self.wave, spectrum=ufunc(*values, **kwargs), metadata=self.metadata)

    def mask(self, maskrange):
        mask = np.where((self.wave > maskrange[0]) * (self.wave < maskrange[1]))
        self.spectrum[mask] = np.nan

@dataclass
class WaterSample():
    reference: list[Spectra] = field(default_factory=list)
    water: list[Spectra] = field(default_factory=list)
    sky : list[Spectra] = field(default_factory=list)
    maxwl : int = field(default=850)
    def _getrhoF(self, wind):
        """ Compute the Fresnel reflectance for a given wind speed"""
        if wind >= 999: wind = 0
        return 0.0256+0.00039*wind+0.000034*wind**2
    
    def getRrs(self, wind):
        _mr = np.mean(self.reference, axis=0)
        _mw = np.mean(self.water, axis=0)
        _ms = np.mean(self.sky, axis=0)

        _sdr = np.std(self.reference, axis=0)
        _sdw = np.std(self.water, axis=0)
        _sds = np.std(self.sky, axis=0)
        
        _rhoF = self._getrhoF(wind)
        _Ed = _mr*np.pi
        
        _Rrs = (_mw-_rhoF*_ms)/_Ed
        _uRrs = np.sqrt(((1/_Ed) * _sdw)**2 +\
                        ((_rhoF/_Ed) * _sds)**2 +\
                        (((_mw-_rhoF*_ms)/_Ed**2) * _sdr)**2)

        _wave = self.reference[0].wave
        _Rrs = _Rrs[_wave <= self.maxwl]
        _uRrs = _uRrs[_wave <= self.maxwl]
        _wave = _wave[_wave <= self.maxwl]
        
        self.Rrs : Spectra = Spectra(name="Rrs", wave=_wave, spectrum=_Rrs, metadata=None)
        self.uRrs : Spectra = Spectra(name="uRrs", wave=_wave, spectrum=_uRrs, metadata=None)
        self.rRrs : Spectra = Spectra(name="uRrs", wave=_wave, spectrum=100*_uRrs/_Rrs, metadata=None)
        
def readASD(path, name=""):
    # Open raw file
    with open(path, 'rb') as f:
        _binconts  = f.read()
    
    # Read metadata
    metadata = ASDmetadata(_binconts)

    #return metadata
    
    # Read spectra
    if metadata.data_format == "DOUBLE_FORMAT":
        _fmt = 'd'*metadata.channels
        _size = 8
    if metadata.data_format == "FLOAT_FORMAT":
        _fmt = 'f'*metadata.channels
        _size = 4


    wave = np.linspace(metadata.ch1_wave, metadata.ch1_wave+metadata.wave_step*metadata.channels-1, metadata.channels)
    # Convierto de binario a array
    spectrum = np.array(struct.unpack(_fmt, _binconts[484:(484 +  metadata.channels*_size)]))
    
    return Spectra("rad", wave, spectrum, metadata)

def calibrateASD(DN, ref, ill, raw):
    IG = np.ones(DN.metadata.channels) * (2048/DN.metadata.swir1_gain)
    IG[DN.wave>DN.metadata.splice2_wavelength] = (2048/DN.metadata.swir2_gain)
    IG[DN.wave<=DN.metadata.splice1_wavelength] = DN.metadata.integration_time
    IG = Spectra(name="offset", spectrum=IG, wave=DN.wave, metadata=None)
    IGr = np.ones(raw.metadata.channels) * (2048/raw.metadata.swir1_gain)
    IGr[raw.wave>raw.metadata.splice2_wavelength] = (2048/raw.metadata.swir2_gain)
    IGr[raw.wave<=raw.metadata.splice1_wavelength] = (raw.metadata.integration_time)
    IGr = Spectra(name="offset", spectrum=IGr, wave=raw.wave, metadata=None)
    
    
    OF = np.zeros(DN.metadata.channels)
    OF = Spectra(name="offset", spectrum=OF, wave=DN.wave, metadata=None)
    OFr = np.zeros(raw.metadata.channels)
    OFr = Spectra(name="offset", spectrum=OFr, wave=raw.wave, metadata=None)

    L = (ref*ill*(DN-OF))/(np.pi*(raw-OFr))*IGr/IG
    setattr(L, "metadata", DN.metadata)
    return L

def parabolicASD(L, xv1=675, xv2=1975):
    # Splice 1
    xO =  L.metadata.splice1_wavelength+1
    xU =  L.metadata.splice1_wavelength
    yO = L.spectrum[L.wave == xO]
    yU = L.spectrum[L.wave == xU]
    x = L.wave
    yp1 = (x-xv1)**2 / (xO-xv1)**2 * (yO-yU) / (yU) + 1
    yp1[L.wave < xv1] = 1
    yp1[L.wave > L.metadata.splice1_wavelength] = 1
    
    # Splice 2
    xO =  L.metadata.splice2_wavelength+1
    xU =  L.metadata.splice2_wavelength-1
    yO = L.spectrum[L.wave == xO]
    yU = L.spectrum[L.wave == xU]
    x = L.wave
    yp2 = (x-xv2)**2 / (xO-xv2)**2 * (yU-yO) / (yO) + 1
    yp2[L.wave > xv2] = 1
    yp2[L.wave <= L.metadata.splice2_wavelength] = 1
    
    yp = Spectra("parabolic", x, yp1*yp2, metadata=None)
    Lp = L*yp
    setattr(Lp, "metadata", Lp)
    return Lp
