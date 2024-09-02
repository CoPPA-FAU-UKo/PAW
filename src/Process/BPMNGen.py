from typing import Tuple
import pm4py
import random
import uuid
from pm4py.objects.bpmn.obj import BPMN
from pm4py.util import constants
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd


class BPMNGenerator:
    def __init__(self, num_node=10, branch_ratio=0.5, seq_ratio=0.3, xor_ratio=0.3,
                 and_ratio=0.3, loop_ratio=0.1, empty_loop_ratio=0.5, fix_name=False):

        self.num_node = num_node
        self.branch_ratio = branch_ratio
        self.seq_ratio = seq_ratio
        self.xor_ratio = xor_ratio
        self.and_ratio = and_ratio
        self.loop_ratio = loop_ratio
        self.empty_loop_ratio = empty_loop_ratio
        self.fix_name = fix_name
        self.rd = random.Random()

    def set_parameter(self, num_node=10, branch_ratio=0.5, seq_ratio=0.3,
                      xor_ratio=0.3, and_ratio=0.3, loop_ratio=0.1, empty_loop_ratio=0.5):
        self.num_node = num_node
        self.branch_ratio = branch_ratio
        self.seq_ratio = seq_ratio
        self.xor_ratio = xor_ratio
        self.and_ratio = and_ratio
        self.loop_ratio = loop_ratio
        self.empty_loop_ratio = empty_loop_ratio

    def generate_sub_sequence(self, bpmn_canvas, len_sub1, len_sub2):
        head_sub1, tail_sub1, seed1 = self.generate_process(bpmn_canvas, len_sub1)
        head_sub2, tail_sub2, seed2 = self.generate_process(bpmn_canvas, len_sub2)
        bpmn_canvas.add_flow(pm4py.objects.bpmn.obj.BPMN.Flow(tail_sub1, head_sub2))
        return head_sub1, tail_sub2, [*seed1, *seed2]

    def generate_task_sequence(self, bpmn_canvas, len_sub=0, seed=[]):
        if len(seed) > 0:
            if seed[0][0] != "s":
                raise RuntimeError("Seed doesn't match")
            seed_seg = seed[0][1:].split("-")
            len_sub1 = int(seed_seg[0])
            node_id = seed_seg[1]
            seed_sub1 = seed[1:1 + len_sub1]
            head_sub1, tail_sub1, seed1 = self.generate_from_seed(bpmn_canvas, seed_sub1)
        else:
            head_sub1, tail_sub1, seed1 = self.generate_process(bpmn_canvas, len_sub - 1)
            node_id = uuid.uuid4().hex[:5]
            if self.fix_name:
                node_id = uuid.UUID(int=self.rd.getrandbits(128), version=4).hex[:5]

        task_node = pm4py.objects.bpmn.obj.BPMN.Task(id="Task_" + node_id, name="Task_" + node_id)
        bpmn_canvas.add_node(task_node)
        bpmn_canvas.add_flow(pm4py.objects.bpmn.obj.BPMN.Flow(task_node, head_sub1))
        return task_node, tail_sub1, ["t" + "-" + node_id, *seed1]

    def generate_loop(self, bpmn_canvas, len_sub1=0, len_sub2=0, seed=[]):
        dir_diver = pm4py.objects.bpmn.obj.BPMN.Gateway.Direction.DIVERGING
        dir_conver = pm4py.objects.bpmn.obj.BPMN.Gateway.Direction.CONVERGING
        seed_sub2 = []
        if len(seed) > 0:
            if seed[0][0] != "l":
                raise RuntimeError("Seed doesn't match")

            seed_seg = seed[0][1:].split("-")
            # empty loop
            len_sub1 = int(seed_seg[0])
            seed_sub1 = seed[1:1 + len_sub1]
            if len(seed_seg) > 3:
                len_sub2 = int(seed_seg[1])
                seed_sub2 = seed[1 + len_sub1:1 + len_sub1 + len_sub2]
            head_sub1, tail_sub1, seed1 = self.generate_from_seed(bpmn_canvas, seed_sub1)
            node_id1 = seed_seg[-2]
            node_id2 = seed_seg[-1]
        else:
            head_sub1, tail_sub1, seed1 = self.generate_process(bpmn_canvas, len_sub1, looping=True)
            node_id1 = uuid.uuid4().hex[:5]
            node_id2 = uuid.uuid4().hex[:5]

        gate_diver = pm4py.objects.bpmn.obj.BPMN.ExclusiveGateway(id="Gateway_" + node_id1,
                                                                  name="Xor_div_" + node_id1,
                                                                  gateway_direction=dir_diver)

        gate_conver = pm4py.objects.bpmn.obj.BPMN.ExclusiveGateway(id="Gateway_" + node_id2,
                                                                   name="Xor_conv_" + node_id2,
                                                                   gateway_direction=dir_conver)
        bpmn_canvas.add_node(gate_diver)
        bpmn_canvas.add_node(gate_conver)
        bpmn_canvas.add_flow(pm4py.objects.bpmn.obj.BPMN.Flow(gate_conver, head_sub1))
        bpmn_canvas.add_flow(pm4py.objects.bpmn.obj.BPMN.Flow(tail_sub1, gate_diver))

        if len_sub2 == 0:

            bpmn_canvas.add_flow(pm4py.objects.bpmn.obj.BPMN.Flow(gate_diver, gate_conver))
            return gate_conver, gate_diver, ["l" + str(len(seed1)) + "-" + node_id1 + "-" + node_id2, *seed1]

        else:
            if len(seed_sub2) > 0:
                head_sub2, tail_sub2, seed2 = self.generate_from_seed(bpmn_canvas, seed_sub2)
            else:
                head_sub2, tail_sub2, seed2 = self.generate_process(bpmn_canvas, len_sub2, looping=True)
            bpmn_canvas.add_flow(pm4py.objects.bpmn.obj.BPMN.Flow(gate_diver, head_sub2))
            bpmn_canvas.add_flow(pm4py.objects.bpmn.obj.BPMN.Flow(tail_sub2, gate_conver))
            return gate_conver, gate_diver, [
                "l" + str(len(seed1)) + "-" + str(len(seed2)) + "-" + node_id1 + "-" + node_id2,
                *seed1, *seed2]

    def generate_branch(self, bpmn_canvas, len_sub1=0, len_sub2=0, gate="p", seed=[]):
        dir_diver = pm4py.objects.bpmn.obj.BPMN.Gateway.Direction.DIVERGING
        dir_conver = pm4py.objects.bpmn.obj.BPMN.Gateway.Direction.CONVERGING

        if len(seed) > 0:
            seed_seg = seed[0][1:].split("-")
            len_sub1 = int(seed_seg[0])
            len_sub2 = int(seed_seg[1])
            seed_sub1 = seed[1: 1 + len_sub1]
            seed_sub2 = seed[1 + len_sub1: 1 + len_sub1 + len_sub2]
            node_id1 = seed_seg[-2]
            node_id2 = seed_seg[-1]
            head_sub1, tail_sub1, seed1 = self.generate_from_seed(bpmn_canvas, seed_sub1)
            head_sub2, tail_sub2, seed2 = self.generate_from_seed(bpmn_canvas, seed_sub2)
        else:
            head_sub1, tail_sub1, seed1 = self.generate_process(bpmn_canvas, len_sub1)
            head_sub2, tail_sub2, seed2 = self.generate_process(bpmn_canvas, len_sub2)
            node_id1 = uuid.uuid4().hex[:5]
            node_id2 = uuid.uuid4().hex[:5]
        if gate == "p":
            gate_diver = pm4py.objects.bpmn.obj.BPMN.ParallelGateway(id="Gateway_" + node_id1,
                                                                     name="And_div_" + node_id1,
                                                                     gateway_direction=dir_diver)
            gate_conver = pm4py.objects.bpmn.obj.BPMN.ParallelGateway(id="Gateway_" + node_id2,
                                                                      name="And_conv_" + node_id2,
                                                                      gateway_direction=dir_conver)
        if gate == "x":
            gate_diver = pm4py.objects.bpmn.obj.BPMN.ExclusiveGateway(id="Gateway_" + node_id1,
                                                                      name="Xor_div_" + node_id1,
                                                                      gateway_direction=dir_diver)
            gate_conver = pm4py.objects.bpmn.obj.BPMN.ExclusiveGateway(id="Gateway_" + node_id2,
                                                                       name="Xor_conv_" + node_id2,
                                                                       gateway_direction=dir_conver)
        bpmn_canvas.add_node(gate_diver)
        bpmn_canvas.add_node(gate_conver)
        bpmn_canvas.add_flow(pm4py.objects.bpmn.obj.BPMN.Flow(gate_diver, head_sub1))
        bpmn_canvas.add_flow(pm4py.objects.bpmn.obj.BPMN.Flow(gate_diver, head_sub2))
        bpmn_canvas.add_flow(pm4py.objects.bpmn.obj.BPMN.Flow(tail_sub1, gate_conver))
        bpmn_canvas.add_flow(pm4py.objects.bpmn.obj.BPMN.Flow(tail_sub2, gate_conver))
        return gate_diver, gate_conver, [gate + str(len(seed1)) + "-" + str(len(seed2)) + "-" + node_id1 + "-" + node_id2,
                                         *seed1, *seed2]

    def generate_process(self, bpmn_canvas, num_node=0, looping=False):
        # generate sub sequence
        if num_node > 1:
            # calculate sub sequences length and seed
            len_sub1 = int(random.uniform(0., 1.) * (num_node - 2)) + 1
            len_sub2 = num_node - len_sub1
            branch_flag = random.uniform(0., 1.) < self.branch_ratio and not looping
            # generate two separate sub sequence and concatenate them
            if branch_flag:
                return self.generate_sub_sequence(bpmn_canvas, len_sub1, len_sub2)

            else:
                random_num = random.uniform(0., 1.)
                if looping:
                    random_num = random.uniform(self.and_ratio + self.xor_ratio, 1.)

                # generate xor
                if random_num < self.xor_ratio:
                    return self.generate_branch(bpmn_canvas, len_sub1, len_sub2, gate="x")

                # generate parallel
                random_num = random_num - self.xor_ratio
                if random_num < self.and_ratio:
                    return self.generate_branch(bpmn_canvas, len_sub1, len_sub2, gate="p")

                # generate loop structure
                random_num = random_num - self.and_ratio
                if random_num < self.loop_ratio:
                    # empty loop
                    if random.random() < self.empty_loop_ratio and not looping:
                        return self.generate_loop(bpmn_canvas, num_node)

                    # sub sequence loop
                    else:
                        return self.generate_loop(bpmn_canvas, len_sub1, len_sub2)

                # generate one task in sequence and keep generating sub sequence
                return self.generate_task_sequence(bpmn_canvas, num_node)

        # return sub sequence with exact one task
        if num_node == 1:
            node_id = uuid.uuid4().hex[:5]
            if self.fix_name:
                node_id = uuid.UUID(int=self.rd.getrandbits(128), version=4).hex[:5]
            task_node = pm4py.objects.bpmn.obj.BPMN.Task(id="Task_" + node_id,
                                                         name="Task_" + node_id)
            bpmn_canvas.add_node(task_node)
            return task_node, task_node, ["t" + "-" + node_id]
        print("Process generator error: empty sub sequence returned")
        # return empty sub sequence
        return None, None, None


    def generate_from_seed(self, bpmn_canvas, seed):

        if len(seed) > 0:
            seq_seed = seed[0]

            # generate one task in sequence and keep generating sub sequence
            if seq_seed[0] == "s":
                return self.generate_task_sequence(bpmn_canvas, seed=seed)

            # generate loop structure
            if seq_seed[0] == "l":
                return self.generate_loop(bpmn_canvas, seed=seed)

            if seq_seed[0] == "p" or seq_seed[0] == "x":
                return self.generate_branch(bpmn_canvas, gate=seq_seed[0], seed=seed)

            # return sub sequence with exact one task
            if seq_seed[0] == "t":
                # print(seed)
                node_id = seq_seed[2:]
                task_node = pm4py.objects.bpmn.obj.BPMN.Task(id=node_id,
                                                             name="Task_" + node_id)
                bpmn_canvas.add_node(task_node)
                if len(seed) == 1:
                    return task_node, task_node, ["t" + "-" + node_id]

                else:
                    seed_sub1 = seed[1:]
                    head_sub1, tail_sub1, seed1 = self.generate_from_seed(bpmn_canvas, seed_sub1)
                    bpmn_canvas.add_flow(pm4py.objects.bpmn.obj.BPMN.Flow(task_node, head_sub1))
                    return task_node, tail_sub1, ["t" + "-" + node_id, *seed1]

        # return empty sub sequence
        return None, None, None

    def create_process(self, seed=""):
        bpmn = pm4py.objects.bpmn.obj.BPMN()
        if self.fix_name:
            node_id = uuid.UUID(int=self.rd.getrandbits(128), version=4).hex[:5]
        else:
            node_id = uuid.uuid4().hex[:5]
        start_node = pm4py.objects.bpmn.obj.BPMN.NormalStartEvent(id="StartEvent_", name=node_id)
        if self.fix_name:
            node_id = uuid.UUID(int=self.rd.getrandbits(128), version=4).hex[:5]
        else:
            node_id = uuid.uuid4().hex[:5]
        end_node = pm4py.objects.bpmn.obj.BPMN.NormalEndEvent(id="EndEvent_", name=node_id)
        bpmn.add_node(start_node)
        bpmn.add_node(end_node)
        if seed == "":
            head_sub, tail_sub, seed = self.generate_process(bpmn, self.num_node)
        else:
            head_sub, tail_sub, seed = self.generate_from_seed(bpmn, seed.split("."))
        bpmn.add_flow(pm4py.objects.bpmn.obj.BPMN.Flow(start_node, head_sub))
        bpmn.add_flow(pm4py.objects.bpmn.obj.BPMN.Flow(tail_sub, end_node))
        return bpmn, ".".join(seed)

    def generate(self, seed="") -> Tuple[BPMN, str]:
        if len(seed) > 0:
            return self.create_process(seed=seed)
        self.rd.seed(0)
        return self.create_process()


def calculate_CFC(seed):
    num_xor = 0
    num_para = 0
    num_loop = 0
    for node in seed.split("."):
        if node[0] == "x":
            num_xor = num_xor + 1
        if node[0] == "p":
            num_para = num_para + 1
        if node[0] == "l":
            num_loop = num_loop + 1

    return 2*num_xor + num_para + 2*num_loop
