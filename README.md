## P2PWifiTopology

### GenerateTopology.py
Generates a topology of nodes (access points). Each node has a list over the nodes it can hear on it's radio, and how loud. The output is in json format, and contains every node in the topology.The node has information about its x,y-coordinates, its name, and its neighbours with their name and intereference measured in -dBi. 

Options:
**-h**, --help,  *show this help message and exit*  
**-x** WIDTH, --width=WIDTH *Width of topology in meters. Default: 500*  
**-y** HEIGHT, --height=HEIGHT *Height of topology in meters. Default: 500*  
**-s** SPACING, --space=SPACING *Minimum spacing between nodes (access points). Default: 10*  
**-n** NODES, --nodes=NODES *Number of nodes. Default: 200 -o OUTPUT, --output=OUTPUT Output filename.*  
**-d** THRESH, --dbithresh=THRESH Absolute value. *Threshold to consider neighbours non-interfering.*  



### CreateGroups.py
Based on the output topology created by `GenerateTopology.py`, this script runs the group creation algorithm and divides the nodes in different groups. The algorithm is performed in iterations, where every group can decide to merge with another group or not. A group can also choose to kick out nodes from their group, should the group size exceed a given threshold. The output is in json format, and contains a list of all the iterations. For every iteration, every group is listed with all its members. 

