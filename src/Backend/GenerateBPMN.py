import src.Process.XMLWriter
from src.Process import BPMNGen
from src.Process import XMLWriter
from pm4py.visualization.bpmn import visualizer as bpmn_visualizer


def generate_BPMN(num_node=10, branch_ratio=0.5, seq_ratio=0.3, xor_ratio=0.3, and_ratio=0.3,
                  loop_ratio=0.1, empty_loop_ratio=0., iteration=1, fix_name=True):

    gen1 = BPMNGen.BPMNGenerator(num_node=num_node, branch_ratio=branch_ratio, seq_ratio=seq_ratio,
                                 xor_ratio=xor_ratio, and_ratio=and_ratio, loop_ratio=loop_ratio,
                                 empty_loop_ratio=empty_loop_ratio, fix_name=fix_name)
    model_list = []
    for i in range(iteration):
        bpmn, seed = gen1.generate()
        model_list.append([bpmn, seed])

    return model_list


def visualization(model, format="png", bgcolor="lavender"):
    parameters = bpmn_visualizer.Variants.CLASSIC.value.Parameters
    gviz = bpmn_visualizer.apply(model, parameters={parameters.FORMAT: format, "bgcolor": bgcolor})
    return gviz


def write_bpmn_to_file(bpmn_list, folder):
    i = 0
    for bpmn in bpmn_list:
        src.Process.XMLWriter.apply(bpmn[0], folder+"/BPMN_"+str(i)+".xml")
        i = i +1
