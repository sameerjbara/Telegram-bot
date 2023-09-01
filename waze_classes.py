import re
import requests

class WazeRouteCalculatorError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class WazeRouteCalculator(object):
    WAZE_URL = "https://www.waze.com/"
    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "referer": WAZE_URL,
    }
    BASE_COORDS = {
        'IL': {"lat": 31.768, "lon": 35.214}
    }
    COORD_SERVERS = {       
        'IL': 'il-SearchServer/mozi'
    }
    ROUTING_SERVERS = {
        'IL': 'il-RoutingManager/routingRequest'
    }

    def __init__(self, start_address, end_address, region='IL', avoid_toll_roads=False):
        region = region.upper()
       
        self.region = region
        self.ROUTE_OPTIONS = {
            'AVOID_TRAILS': 't',
            'AVOID_TOLL_ROADS': 't' if avoid_toll_roads else 'f'
        }
        self.start_coords = self.address_to_coords(start_address)
        self.end_coords = self.address_to_coords(end_address)

    def address_to_coords(self, address):
        base_coords = self.BASE_COORDS[self.region]
        get_cord = self.COORD_SERVERS[self.region]
        url_options = {
            "q": address,
            "lang": "hebrew",
            "origin": "livemap",
            "lat": base_coords["lat"],
            "lon": base_coords["lon"]
        }

        response = requests.get(self.WAZE_URL + get_cord, params=url_options, headers=self.HEADERS)
        for response_json in response.json():
            if response_json.get('city'):
                lat = response_json['location']['lat']
                lon = response_json['location']['lon']
                bounds = response_json.get('bounds', {})
                return {"lat": lat, "lon": lon, "bounds": bounds}
        raise WazeRouteCalculatorError("Cannot get coords for %s" % address)

    def get_route(self, npaths=1, time_delta=0):
        routing_server = self.ROUTING_SERVERS[self.region]

        url_options = {
            "from": "x:%s y:%s" % (self.start_coords["lon"], self.start_coords["lat"]),
            "to": "x:%s y:%s" % (self.end_coords["lon"], self.end_coords["lat"]),
            "at": time_delta,
            "returnJSON": "true",
            "returnGeometries": "true",
            "returnInstructions": "true",
            "subscription": "*",
            "timeout": 60000,
            "nPaths": npaths,
            "options": ','.join('%s:%s' % (opt, value) for (opt, value) in self.ROUTE_OPTIONS.items()),
        }
        response = requests.get(self.WAZE_URL + routing_server, params=url_options, headers=self.HEADERS)
        response.encoding = 'utf-8'
        
        if response.ok:
            response_json = response.json()
            if 'error' in response_json:
                raise WazeRouteCalculatorError(response_json.get("error"))
            else:
                if response_json.get("alternatives"):
                    return [alt['response'] for alt in response_json['alternatives']]
                response_obj = response_json['response']
                if isinstance(response_obj, list):
                    response_obj = response_obj[0]
                if npaths > 1:
                    return [response_obj]
                return response_obj
        else:
            raise WazeRouteCalculatorError("HTTP request failed with status code: {}".format(response.status_code))

    def _add_up_route(self, results, real_time=True, stop_at_bounds=False):
        start_bounds = self.start_coords['bounds']
        end_bounds = self.end_coords['bounds']

        def between(target, min, max):
            return target > min and target < max

        time = 0
        distance = 0
        for segment in results:
            if stop_at_bounds and segment.get('path'):
                x = segment['path']['x']
                y = segment['path']['y']
                if (
                    between(x, start_bounds.get('left', 0), start_bounds.get('right', 0)) or
                    between(x, end_bounds.get('left', 0), end_bounds.get('right', 0))
                ) and (
                    between(y, start_bounds.get('bottom', 0), start_bounds.get('top', 0)) or
                    between(y, end_bounds.get('bottom', 0), end_bounds.get('top', 0))
                ):
                    continue
            if 'crossTime' in segment:
                time += segment['crossTime' if real_time else 'crossTimeWithoutRealTime']
            else:
                time += segment['cross_time' if real_time else 'cross_time_without_real_time']
            distance += segment['length']
        route_time = time / 60.0
        route_distance = distance / 1000.0
        return route_time, route_distance

    def calc_route_info(self, real_time=True, stop_at_bounds=False, time_delta=0):
        route = self.get_route(1, time_delta)
        results = route['results' if 'results' in route else 'result']
        route_time, route_distance = self._add_up_route(results, real_time=real_time, stop_at_bounds=stop_at_bounds)
        return route_time, route_distance
