TABLE_KEY_MAP = {
    "cpo_net": "imsi",
    "cpo_next_charge": "msisdn",
    "cpo_services": "imsi",
    "cpo_ep_products": "msisdn",
    "cpo_ep_quotas": "msisdn",
    "cpo_mts_id": "msisdn",
    "cpo_my_mts": "guid",
    "cpo_mtsa_music": "guid",
}

SCENARIO_TABLES_MAP_PRIVACY = {
    "slow_data": ("cpo_net",),
    "fast_data": ("dragonfly",),
    "full_data": ("cpo_net", "dragonfly"),
    "mixed_sample": ("cpo_net",),
    "my_mts_info": ("cpo_my_mts",),
    "my_mts_info_limit": ("cpo_my_mts",),
    "mts_music": ("cpo_mtsa_music",),
    "mts_music_limit": ("cpo_mtsa_music",),
    "recsys": ("cpo_next_charge", "cpo_services", "cpo_ep_products"),
}

SCENARIO_TABLES_MAP_PUBLIC = {
    "slow_data": ("cpo_my_mts", "cpo_mtsa_music"),
    "fast_data": ("dragonfly",),
    "full_data": ("cpo_my_mts", "cpo_mtsa_music", "dragonfly"),
    "mixed_sample": ("cpo_my_mts", "cpo_mtsa_music"),
    "my_mts_info": ("cpo_my_mts",),
    "my_mts_info_limit": ("cpo_my_mts",),
    "mts_music": ("cpo_mtsa_music",),
    "mts_music_limit": ("cpo_mtsa_music",),
    "recsys": ("cpo_my_mts", "cpo_mtsa_music"),
}

_CPO_NET = {
    "msisdnRaw": True,
    "msisdnDict": True,
    "imei": True,
    "regionName": True,
    "cityName": True,
    "regionUpdated": True,
    "countryName": True,
    "countryNameUpdated": True,
    "homeWorkStatus": True,
    "homeWorkStatusUpdated": True,
}

_CPO_SERVICES = {
    "services": True,
}

_NEXT_CHARGES = {
    "nextCharges": True
}

_RECENT_AUTHENTICATIONS = {
    "recentAuthentications": True
}

_EP_PRODUCTS = {
    "epProducts": True
}

_MTSA_MUSIC_INFO = {
    "mtsaMusicInfo": True
}

_MY_MTS_INFO = {
    "myMtsInfo": True
}

_SERVICE_REQUEST_HISTORY = {
    "serviceRequestHistory": True
}

_CPO_GEO_DATA = {
    "lac": True,
    "cell": True,
    "lacCellUpdated": True,
    "lat": True,
    "lon": True,
    "radius": True,
    "latLonUpdated": True,
    "utcOffset": True,
    "utcOffsetUpdated": True,
}

_CPO_CLICKSTREAM = {
    "host": True,
    "hostUpdated": True,
    "businessHost": True,
    "businessHostUpdated": True,
}

_CASSANDRA_DATA = {
    **_CPO_NET,
    **_CPO_SERVICES,
    **_NEXT_CHARGES,
    **_RECENT_AUTHENTICATIONS,
    **_EP_PRODUCTS,
    **_MTSA_MUSIC_INFO,
    **_MY_MTS_INFO,
    **_SERVICE_REQUEST_HISTORY,

}

_DRAGONFLY_DATA = {
    **_CPO_GEO_DATA,
    **_CPO_CLICKSTREAM
}

_PUBLIC_FIELDS = {
    "guid": True,
    "imei": True,
    "nextCharges": True,
    "services": True,
    "recentAuthentications": True,
    "epProducts": True,
    "mtsaMusicInfo": True,
}

_MIXED_SAMPLE_PRIVACY = {
    "lac": True,
    "imei": True,
}


_MIXED_SAMPLE_PUBLIC = {
    "imei": True,
}

SCENARIO_BODY_MAP_PRIVACY = {
    "full_data": {},
    "slow_data": _CASSANDRA_DATA,
    "fast_data": _DRAGONFLY_DATA,
    "mixed_sample": _MIXED_SAMPLE_PRIVACY,
    "my_mts_info": _MY_MTS_INFO,
    "my_mts_info_limit":
        {
            "myMtsInfo": {
                "args": {
                    "limit": 1
                }
            }
        },
    "mts_music": _MTSA_MUSIC_INFO,
    "mts_music_limit":
        {
            "mtsaMusicInfo": {
                "args": {
                    "limit": 1
                }
            }
        },
    "recsys": {
        "epProducts": True,
        "services": True,
        "nextCharges": True,
    },
}

SCENARIO_BODY_MAP_PUBLIC = {
    "slow_data": None, # это будет дублем full_data
    "fast_data": None,
    "full_data": _PUBLIC_FIELDS,
    "mixed_sample": _MIXED_SAMPLE_PUBLIC,
    "my_mts_info": _MY_MTS_INFO,
    "my_mts_info_limit":
        {
            "myMtsInfo": {
                "args": {
                    "limit": 1
                }
            }
        },
    "mts_music": _MTSA_MUSIC_INFO,
    "mts_music_limit":
        {
            "mtsaMusicInfo": {
                "args": {
                    "limit": 1
                }
            }
        },
    "recsys": {
        "epProducts": True,
        "services": True,
        "nextCharges": True,
    },
}
