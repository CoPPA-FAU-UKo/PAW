



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