import uuid
from pm4py.objects.bpmn.obj import BPMN
from pm4py.util import constants
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd


def apply(bpmn_graph, target_path):
    xml_string = get_xml_string(bpmn_graph)
    F = open(target_path, "wb")
    F.write(xml_string)
    F.close()


def get_xml_string(bpmn_graph):
    definitions = ET.Element("bpmn:definitions")
    definitions.set("xmlns:bpmn", "http://www.omg.org/spec/BPMN/20100524/MODEL")
    definitions.set("xmlns:bpmndi", "http://www.omg.org/spec/BPMN/20100524/DI")
    definitions.set("xmlns:omgdc", "http://www.omg.org/spec/DD/20100524/DC")
    definitions.set("xmlns:omgdi", "http://www.omg.org/spec/DD/20100524/DI")
    definitions.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    definitions.set("targetNamespace", "http://www.signavio.com/bpmn20")
    definitions.set("typeLanguage", "http://www.w3.org/2001/XMLSchema")
    definitions.set("expressionLanguage", "http://www.w3.org/1999/XPath")
    definitions.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")
    definitions.set("xmlns:zeebe", "http://camunda.org/schema/zeebe/1.0")


    all_processes = set()
    process_planes = {}
    process_process = {}
    for node in bpmn_graph.get_nodes():
        all_processes.add(node.get_process())

    for process in all_processes:
        p = ET.SubElement(definitions, "bpmn:process",
                          {"id": "id" + process, "isClosed": "false", "isExecutable": "true",
                           "processType": "None"})
        process_process[process] = p

    diagram = ET.SubElement(definitions, "bpmndi:BPMNDiagram", {"id": "id" + str(uuid.uuid4()), "name": "diagram"})

    for process in all_processes:
        plane = ET.SubElement(diagram, "bpmndi:BPMNPlane",
                              {"bpmnElement": "id" + process, "id": "Process_" + str(uuid.uuid4())})
        process_planes[process] = plane

    for node in bpmn_graph.get_nodes():
        process = node.get_process()

        node_shape = ET.SubElement(process_planes[process], "bpmndi:BPMNShape",
                                   {"bpmnElement": node.get_id(), "id": node.get_id() + "_gui"})
        node_shape_layout = ET.SubElement(node_shape, "omgdc:Bounds",
                                          {"height": str(node.get_height()), "width": str(node.get_width()),
                                           "x": str(node.get_x()),
                                           "y": str(node.get_y())})

    for flow in bpmn_graph.get_flows():
        process = flow.get_process()

        flow_shape = ET.SubElement(process_planes[process], "bpmndi:BPMNEdge",
                                   {"bpmnElement": "SequenceFlow_" + str(flow.get_id()),
                                    "id": "SequenceFlow_" + str(flow.get_id()) + "_gui"})
        for x, y in flow.get_waypoints():
            waypoint = ET.SubElement(flow_shape, "omgdi:waypoint", {"x": str(x), "y": str(y)})

    for node in bpmn_graph.get_nodes():
        process = process_process[node.get_process()]

        if isinstance(node, BPMN.StartEvent):
            isInterrupting = "true" if node.get_isInterrupting() else "false"
            parallelMultiple = "true" if node.get_parallelMultiple() else "false"
            task = ET.SubElement(process, "bpmn:startEvent",
                                 {"id": node.get_id(), "isInterrupting": isInterrupting, "name": node.get_name(),
                                  "parallelMultiple": parallelMultiple})
        elif isinstance(node, BPMN.EndEvent):
            task = ET.SubElement(process, "bpmn:endEvent", {"id": node.get_id(), "name": node.get_name()})
        elif isinstance(node, BPMN.IntermediateCatchEvent):
            task = ET.SubElement(process, "bpmn:intermediateCatchEvent", {"id": node.get_id(), "name": node.get_name()})
        elif isinstance(node, BPMN.IntermediateThrowEvent):
            task = ET.SubElement(process, "bpmn:intermediateThrowEvent", {"id": node.get_id(), "name": node.get_name()})
        elif isinstance(node, BPMN.BoundaryEvent):
            task = ET.SubElement(process, "bpmn:boundaryEvent", {"id": node.get_id(), "name": node.get_name()})
        elif isinstance(node, BPMN.Task):
            task = ET.SubElement(process, "bpmn:userTask", {"id": node.get_id(), "name": node.get_name()})
        elif isinstance(node, BPMN.SubProcess):
            task = ET.SubElement(process, "bpmn:subProcess", {"id": node.get_id(), "name": node.get_name()})
        elif isinstance(node, BPMN.ExclusiveGateway):
            task = ET.SubElement(process, "bpmn:exclusiveGateway",
                                 {"id": node.get_id(), "gatewayDirection": node.get_gateway_direction().value,
                                  "name": ""})
        elif isinstance(node, BPMN.ParallelGateway):
            task = ET.SubElement(process, "bpmn:parallelGateway",
                                 {"id": node.get_id(), "gatewayDirection": node.get_gateway_direction().value,
                                  "name": ""})
        elif isinstance(node, BPMN.InclusiveGateway):
            task = ET.SubElement(process, "bpmn:inclusiveGateway",
                                 {"id": node.get_id(), "gatewayDirection": node.get_gateway_direction().value,
                                  "name": ""})
        else:
            raise Exception("Unexpected node type.")

        for in_arc in node.get_in_arcs():
            arc_xml = ET.SubElement(task, "bpmn:incoming")
            arc_xml.text = "SequenceFlow_" + str(in_arc.get_id())

        for out_arc in node.get_out_arcs():
            arc_xml = ET.SubElement(task, "bpmn:outgoing")
            arc_xml.text = "SequenceFlow_" + str(out_arc.get_id())

    true_list = []
    for flow in bpmn_graph.get_flows():
        process = process_process[flow.get_process()]

        source = flow.get_source()
        target = flow.get_target()
        flow_xml = ET.SubElement(process, "bpmn:sequenceFlow", {"id": "SequenceFlow_" + str(flow.get_id()), "name": flow.get_name(),
                                                                "sourceRef": str(source.get_id()),
                                                                "targetRef": str(target.get_id())})

        if isinstance(source, BPMN.ExclusiveGateway):
            if source.get_gateway_direction().value != "Converging":
                expression = ET.SubElement(flow_xml, "bpmn:conditionExpression",{"xsi:type":"bpmn:tFormalExpression"})
                if str(source.get_id()) not in true_list:
                    expression.text = "=v" + str(source.get_id()) + " = true"
                    true_list.append(str(source.get_id()))
                else:
                    expression.text = "=v" + str(source.get_id()) + " = false"

    return minidom.parseString(ET.tostring(definitions)).toprettyxml(encoding=constants.DEFAULT_ENCODING)

