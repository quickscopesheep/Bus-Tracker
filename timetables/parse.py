import xml.etree.cElementTree as ET
import isodate
from datetime import datetime, timedelta

#global variable, messy but should work
xml_namespace = {'tx': 'http://www.transxchange.org.uk/'}

class Stop:
    def __init__(self, e : ET.Element):
        self.name = e.findtext('tx:CommonName', namespaces=xml_namespace)
        self.atco = e.findtext('tx:StopPointRef', namespaces=xml_namespace)
        self.locality = e.findtext('tx:LocalityName', namespaces=xml_namespace)

#NOT NEEDED FOR TIMETABLE DATA
#class RouteLink:
#    def __init__(self, e : ET.Element):
#        self.id = e.get('id')
#        self.from_stop = e.findtext('To/StopPointRef')
#        self.to_stop = e.findtext('To/StopPointRef')
#
#        #todo parse path takes between stops
#
#class RouteSection:
#    def __init__(self, e : ET.Element):
#        self.id = e.get('id')
#        self.links = [RouteLink(link) for link in e.findall('RouteLink')]
#
#class Route:
#    def __init__(self, e : ET.Element):
#        self.id = e.get('id')
#        self.sections = [section.text for section in e.findall('RouteSectionRef')]
#    pass

class JourneyPatternTimingLink:
    def __init__(self, e : ET.Element):
        self.id = e.get('id')
        self.from_stop = e.findtext('tx:From/tx:StopPointRef', namespaces=xml_namespace)
        self.to_stop = e.findtext('tx:To/tx:StopPointRef', namespaces=xml_namespace)

        self.runtime = isodate.parse_duration(e.findtext('tx:RunTime', namespaces=xml_namespace))

        self.route_ref = e.findtext('tx:RouteLinkRef', namespaces=xml_namespace)

class JourneyPatternSection:
    def __init__(self, e : ET.Element):
        self.id = e.get('id')
        self.timing_links = [JourneyPatternTimingLink(link) for link in e.findall('tx:JourneyPatternTimingLink', namespaces=xml_namespace)]

class JourneyPattern:
    def __init__(self, journey_pattern_sections, e : ET.Element):
        self.id = e.get('id')
        self.destination_text = e.findtext('tx:DestinationDisplay', namespaces=xml_namespace)
        self.direction = e.findtext('tx:Direction', namespaces=xml_namespace)
        self.pattern_sections = [journey_pattern_sections[ref.text] for ref in e.findall('tx:JourneyPatternSectionRefs', namespaces=xml_namespace)]

class Line:
    def __init__(self, e : ET.Element):
        self.id = e.get('id')
        self.name = e.findtext('tx:LineName', namespaces=xml_namespace)

        self.outbound_desc = e.findtext('tx:OutboundDescription/tx:Description', namespaces=xml_namespace)
        self.inbound_desc = e.findtext('tx:InboundDescription/tx:Description', namespaces=xml_namespace)

class Service:
    def __init__(self, journey_pattern_sections, e : ET.Element):
        self.operator = e.findtext('tx:RegisteredOperatorRef', namespaces=xml_namespace)
        self.service_code = e.findtext('tx:ServiceCode', namespaces=xml_namespace)

        self.origin = e.findtext('tx:StandardService/tx:Origin', namespaces=xml_namespace)
        self.dest = e.findtext('tx:StandardService/tx:Destination', namespaces=xml_namespace)

        vias = e.find('tx:StandardService/tx:Vias', namespaces=xml_namespace)
        if vias != None:
            self.vias = [via.text for via in vias]
        else:
            self.vias = None

        patterns = [JourneyPattern(journey_pattern_sections, pattern) for pattern in e.findall('tx:StandardService/tx:JourneyPattern', namespaces=xml_namespace)]
        self.journey_patterns = {
            journey_pattern.id : journey_pattern for journey_pattern in patterns
        }

        self.lines = [Line(line) for line in e.find('tx:Lines', namespaces=xml_namespace)]
    pass

class JourneyTimingLink:
    def __init__(self, e : ET.Element):
        self.pattern_timing_link_ref = e.findtext('tx:JourneyPatternTimingLinkRef', namespaces=xml_namespace)
        self.runtime = isodate.parse_duration(e.findtext('tx:RunTime', namespaces=xml_namespace))

        to_waittime_text = e.findtext('tx:To/tx:WaitTime', namespaces=xml_namespace)

        if to_waittime_text != None: self.to_waittime = isodate.parse_duration(to_waittime_text)
        else: self.to_waittime = timedelta()

        from_waittime_text = e.findtext('tx:From/tx:WaitTime', namespaces=xml_namespace)
        if from_waittime_text != None: self.from_waittime = isodate.parse_duration(from_waittime_text)
        else: self.from_waittime = timedelta()

#our own data structure
class TimingPoint:
    def __init__(self, atco, common_name, arrival_time, departure_time):
        self.atco = atco
        self.common_name = common_name
        self.arrival_time = arrival_time
        self.departure_time = departure_time

    def __str__(self):
        return f'[Name : {self.common_name}, Atco: {self.atco}, Arrival Time: {self.arrival_time}, Departure Time: {self.departure_time}]'

class Journey:
    def __init__(self, services : dict[Service], stops : dict[Stop], e : ET.Element):
        self.stops = stops

        self.code = e.findtext('tx:VehicleJourneyCode', namespaces=xml_namespace)
        self.private_code = e.findtext('tx:PrivateCode', namespaces=xml_namespace)

        self.sequence_number = int(e.get('SequenceNumber'))

        self.service_ref = e.findtext('tx:ServiceRef', namespaces=xml_namespace)
        self.line_ref = e.findtext('tx:LineRef', namespaces=xml_namespace)

        self.departure_time_text = e.findtext('tx:DepartureTime', namespaces=xml_namespace)
        
        #TODO: handle times close to midnight
        self.departure_time = datetime.strptime(self.departure_time_text, "%H:%M:%S").time()

        self.is_deadrun = e.findtext('tx:JourneyPurpose', namespaces=xml_namespace) in ['deadRun', 'garageRun']

        journey_pattern_ref = e.find('tx:JourneyPatternRef', namespaces=xml_namespace)
        if journey_pattern_ref != None:
            self.journey_ref = None
            self.journey_pattern = services[self.service_ref].journey_patterns[journey_pattern_ref.text]
        else:
            self.journey_pattern = None
            self.journey_ref = e.find('tx:VehicleJourneyRef', namespaces=xml_namespace)

        timing_links = [JourneyTimingLink(timing_link_element) for timing_link_element in e.findall('tx:VehicleJourneyTimingLink', namespaces=xml_namespace)]
        self.timing_links = {timing_link.pattern_timing_link_ref : timing_link for timing_link in timing_links}

    #TODO: refactor so array doesnt have to be duplicated
    def get_timing_links(self):
        timing_links = []
        for section in self.journey_pattern.pattern_sections:
            for link in section.timing_links:
                journey_timing_link = self.timing_links.get(link.id)
                timing_links.append((link, journey_timing_link))

        return timing_links
    
    def _add_or_get_point(self, points : dict[TimingPoint], atco):
        point = points.get(atco)
        if point: return point
        else:
            point = TimingPoint(atco, self.stops[atco].name , None, None)
            points[atco] = point
            return point
    
    def get_timetable(self):
        points = {}
        time = datetime.combine(datetime.today(), self.departure_time)

        for (link, journey_timing_link) in self.get_timing_links():
            from_stop = link.from_stop
            to_stop = link.to_stop

            from_point = self._add_or_get_point(points, from_stop)
            to_point = self._add_or_get_point(points, to_stop)

            runtime = None
            if journey_timing_link and journey_timing_link.runtime:
                runtime = journey_timing_link.runtime
            else:
                runtime = link.runtime

            from_wait = journey_timing_link.from_waittime
            to_wait = journey_timing_link.to_waittime

            time += from_wait
            from_point.departure_time = time
            time += runtime
            to_point.arrival_time = time

        return points


class DataSetParser:
    def __init__(self, stream):
        self.tree_iter = ET.iterparse(stream)

        self.stops = {}
        self.services = {}
        self.journeys = []
    
    def _parse_journeys(self, e):
        journeys = {}

        for journey_element in e:
            journey = Journey(self.services, self.stops, journey_element)
            journeys[journey.code] = journey

        for journey in iter(journeys.values()):
            if journey.journey_ref != None:
                journey.journey_pattern = journeys[journey.code].journey_pattern
        
        return [journey for journey in iter(journeys.values())]

    def parse(self):
        journey_pattern_sections = None

        #TODO: ensure JourneyPatternSections always comes before services
        for _, e in self.tree_iter:
            if e.tag.endswith('StopPoints'):
                for stop_element in e:
                    stop = Stop(stop_element)
                    self.stops[stop.atco] = stop
            elif e.tag.endswith('JourneyPatternSections'):
                journey_pattern_sections = {}
                for pattern_section_element in e:
                    pattern_section = JourneyPatternSection(pattern_section_element)
                    journey_pattern_sections[pattern_section.id] = pattern_section
            elif e.tag.endswith('Services'):
                if journey_pattern_sections == None:
                    print('<JourneyPatternSections> Not Read')

                for service_element in e:
                    service = Service(journey_pattern_sections, service_element)
                    self.services[service.service_code] = service
            elif e.tag.endswith('VehicleJourneys'):
                self.journeys = self._parse_journeys(e)

        print(f'parsed {len(self.stops)} stops, {len(self.services)} services, {len(self.journeys)} journeys')