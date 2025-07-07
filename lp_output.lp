MaxProfit:
MAXIMIZE
174188.02999999933*x_Bastion_Module_I + -135212.0*x_Coherent_Asteroid_Mining_Crystal_Type_A_I + -49294.21000000002*x_Coherent_Asteroid_Mining_Crystal_Type_A_II + 277696.0*x_Coherent_Asteroid_Mining_Crystal_Type_B_I + 130836.56999999995*x_Coherent_Asteroid_Mining_Crystal_Type_B_II + -154956.0*x_Complex_Asteroid_Mining_Crystal_Type_A_I + -35108.97999999998*x_Complex_Asteroid_Mining_Crystal_Type_A_II + 240348.0*x_Complex_Asteroid_Mining_Crystal_Type_B_I + 254815.04000000004*x_Complex_Asteroid_Mining_Crystal_Type_B_II + 2280473.33*x_Covert_Cynosural_Field_Generator_I + 41334.32999999996*x_Deep_Core_Mining_Laser_I + 2327196.08*x_Defender_Launcher_I + 172825.88*x_Drone_Link_Augmentor_I + 376957.8999999999*x_Drone_Link_Augmentor_II + 1375869.8200000003*x_Gas_Cloud_Harvester_I + 1364538.0300000003*x_Gas_Cloud_Harvester_II + 2108296.6799999997*x_Industrial_Cynosural_Field_Generator + 925281.9100000001*x_Interdiction_Sphere_Launcher_I + 8097134.6499999985*x_Large_Asteroid_Ore_Compressor_I + 4154896.0199999996*x_Medium_Asteroid_Ore_Compressor_I + 229748.0*x_Mercoxit_Asteroid_Mining_Crystal_Type_A_I + -565889.98*x_Mercoxit_Asteroid_Mining_Crystal_Type_A_II + 729124.0*x_Mercoxit_Asteroid_Mining_Crystal_Type_B_I + 225244.49000000022*x_Modulated_Deep_Core_Miner_II + -991.0094*x_R.A.M.__Electronics + -994.8004000000001*x_R.A.M.__Energy_Tech + -16670.209999999992*x_Simple_Asteroid_Mining_Crystal_Type_A_II + 39504.0*x_Simple_Asteroid_Mining_Crystal_Type_B_I + 326148.57*x_Simple_Asteroid_Mining_Crystal_Type_B_II + 766740.3300000001*x_Small_Tractor_Beam_I + -11576.0*x_Variegated_Asteroid_Mining_Crystal_Type_A_I + 57005.01000000001*x_Variegated_Asteroid_Mining_Crystal_Type_A_II + 258744.0*x_Variegated_Asteroid_Mining_Crystal_Type_B_I + 375998.03*x_Variegated_Asteroid_Mining_Crystal_Type_B_II + 0.0
SUBJECT TO
_C1: 5 x_Drone_Link_Augmentor_II + 15 x_Gas_Cloud_Harvester_II
 + 23 x_Modulated_Deep_Core_Miner_II <= 4918

_C2: 2 x_Deep_Core_Mining_Laser_I + 30 x_Gas_Cloud_Harvester_II <= 3070

_C3: 4.52488687783 x_Coherent_Asteroid_Mining_Crystal_Type_A_II
 + 9.04977375566 x_Coherent_Asteroid_Mining_Crystal_Type_B_II
 + 9.47867298578 x_Complex_Asteroid_Mining_Crystal_Type_A_II
 + 18.9573459716 x_Complex_Asteroid_Mining_Crystal_Type_B_II
 + 4.49438202247 x_Gas_Cloud_Harvester_II
 + 11.8483412322 x_Mercoxit_Asteroid_Mining_Crystal_Type_A_II
 + 4.86618004866 x_Modulated_Deep_Core_Miner_II
 + 4.52488687783 x_Simple_Asteroid_Mining_Crystal_Type_A_II
 + 9.04977375566 x_Simple_Asteroid_Mining_Crystal_Type_B_II
 + 7.10900473934 x_Variegated_Asteroid_Mining_Crystal_Type_A_II
 + 14.2180094787 x_Variegated_Asteroid_Mining_Crystal_Type_B_II <= 1500

_C4: 28453 x_Bastion_Module_I + 1854 x_Covert_Cynosural_Field_Generator_I
 + 1921 x_Deep_Core_Mining_Laser_I + 5521 x_Defender_Launcher_I
 + 53 x_Drone_Link_Augmentor_I + 4268 x_Gas_Cloud_Harvester_I
 + 2182 x_Industrial_Cynosural_Field_Generator
 + 2863 x_Interdiction_Sphere_Launcher_I
 + 34523 x_Large_Asteroid_Ore_Compressor_I
 + 17451 x_Medium_Asteroid_Ore_Compressor_I + 222 x_R.A.M.__Electronics
 + 222 x_R.A.M.__Energy_Tech + 8536 x_Small_Tractor_Beam_I <= 6850983

_C5: 3 x_Modulated_Deep_Core_Miner_II <= 8378

_C6: 12 x_Drone_Link_Augmentor_II <= 2

_C7: 331948 x_Bastion_Module_I + 11896 x_Covert_Cynosural_Field_Generator_I
 + 6442 x_Deep_Core_Mining_Laser_I + 88539 x_Defender_Launcher_I
 + 4743 x_Drone_Link_Augmentor_I + 42679 x_Gas_Cloud_Harvester_I
 + 19201 x_Industrial_Cynosural_Field_Generator
 + 12011 x_Interdiction_Sphere_Launcher_I
 + 129460 x_Large_Asteroid_Ore_Compressor_I
 + 65441 x_Medium_Asteroid_Ore_Compressor_I + 556 x_R.A.M.__Electronics
 + 556 x_R.A.M.__Energy_Tech + 23711 x_Small_Tractor_Beam_I <= 16540605

_C8: 4.30107526882 x_Drone_Link_Augmentor_II <= 500

_C9: 379 x_Bastion_Module_I + 1868 x_Covert_Cynosural_Field_Generator_I
 + 462 x_Defender_Launcher_I + 96 x_Drone_Link_Augmentor_I
 + 257 x_Gas_Cloud_Harvester_I + 409 x_Industrial_Cynosural_Field_Generator
 + 378 x_Interdiction_Sphere_Launcher_I
 + 864 x_Large_Asteroid_Ore_Compressor_I
 + 437 x_Medium_Asteroid_Ore_Compressor_I + 140 x_Small_Tractor_Beam_I
 <= 18317

_C10: 4743 x_Bastion_Module_I + 2016 x_Covert_Cynosural_Field_Generator_I
 + 1423 x_Deep_Core_Mining_Laser_I + 3552 x_Defender_Launcher_I
 + 2 x_Drone_Link_Augmentor_I + 1281 x_Gas_Cloud_Harvester_I
 + 1042 x_Industrial_Cynosural_Field_Generator
 + 1097 x_Interdiction_Sphere_Launcher_I
 + 17262 x_Large_Asteroid_Ore_Compressor_I
 + 8726 x_Medium_Asteroid_Ore_Compressor_I + 82 x_R.A.M.__Electronics
 + 82 x_R.A.M.__Energy_Tech + 2372 x_Small_Tractor_Beam_I <= 204

_C11: 71132 x_Bastion_Module_I + 7153 x_Covert_Cynosural_Field_Generator_I
 + 3370 x_Deep_Core_Mining_Laser_I + 26929 x_Defender_Launcher_I
 + 1897 x_Drone_Link_Augmentor_I + 17072 x_Gas_Cloud_Harvester_I
 + 12248 x_Industrial_Cynosural_Field_Generator
 + 9764 x_Interdiction_Sphere_Launcher_I
 + 129460 x_Large_Asteroid_Ore_Compressor_I
 + 65441 x_Medium_Asteroid_Ore_Compressor_I + 444 x_R.A.M.__Electronics
 + 444 x_R.A.M.__Energy_Tech + 10433 x_Small_Tractor_Beam_I <= 10419102

_C12: 12 x_Drone_Link_Augmentor_II <= 1507

_C13: 190 x_Bastion_Module_I + 1011 x_Covert_Cynosural_Field_Generator_I
 + 369 x_Defender_Launcher_I + 19 x_Drone_Link_Augmentor_I
 + 427 x_Gas_Cloud_Harvester_I + 820 x_Industrial_Cynosural_Field_Generator
 + 228 x_Interdiction_Sphere_Launcher_I
 + 864 x_Large_Asteroid_Ore_Compressor_I
 + 437 x_Medium_Asteroid_Ore_Compressor_I + 76 x_Small_Tractor_Beam_I <= 10578

_C14: 3 x_Deep_Core_Mining_Laser_I + 30 x_Gas_Cloud_Harvester_II <= 15239

_C15: 14 x_Coherent_Asteroid_Mining_Crystal_Type_A_II
 + 18 x_Coherent_Asteroid_Mining_Crystal_Type_B_II
 + 30 x_Complex_Asteroid_Mining_Crystal_Type_A_II
 + 38 x_Complex_Asteroid_Mining_Crystal_Type_B_II
 + 40 x_Mercoxit_Asteroid_Mining_Crystal_Type_A_II
 + 8 x_Simple_Asteroid_Mining_Crystal_Type_A_II
 + 10 x_Simple_Asteroid_Mining_Crystal_Type_B_II
 + 23 x_Variegated_Asteroid_Mining_Crystal_Type_A_II
 + 29 x_Variegated_Asteroid_Mining_Crystal_Type_B_II <= 7344

_C16: 23 x_Gas_Cloud_Harvester_II + 5 x_Modulated_Deep_Core_Miner_II <= 2914

_C17: 949 x_Bastion_Module_I + 214 x_Coherent_Asteroid_Mining_Crystal_Type_A_I
 + 268 x_Coherent_Asteroid_Mining_Crystal_Type_B_I
 + 427 x_Complex_Asteroid_Mining_Crystal_Type_A_I
 + 534 x_Complex_Asteroid_Mining_Crystal_Type_B_I
 + 845 x_Covert_Cynosural_Field_Generator_I + 95 x_Deep_Core_Mining_Laser_I
 + 1321 x_Defender_Launcher_I + 2 x_Drone_Link_Augmentor_I
 + 513 x_Gas_Cloud_Harvester_I + 463 x_Industrial_Cynosural_Field_Generator
 + 553 x_Interdiction_Sphere_Launcher_I
 + 864 x_Large_Asteroid_Ore_Compressor_I
 + 437 x_Medium_Asteroid_Ore_Compressor_I
 + 759 x_Mercoxit_Asteroid_Mining_Crystal_Type_A_I
 + 1067 x_Mercoxit_Asteroid_Mining_Crystal_Type_B_I + 36 x_R.A.M.__Electronics
 + 36 x_R.A.M.__Energy_Tech + 107 x_Simple_Asteroid_Mining_Crystal_Type_B_I
 + 333 x_Small_Tractor_Beam_I
 + 342 x_Variegated_Asteroid_Mining_Crystal_Type_A_I
 + 427 x_Variegated_Asteroid_Mining_Crystal_Type_B_I <= 1002

_C18: 4.49438202247 x_Gas_Cloud_Harvester_II
 + 4.86618004866 x_Modulated_Deep_Core_Miner_II <= 500

_C19: 4.30107526882 x_Drone_Link_Augmentor_II <= 500

_C20: 4.52488687783 x_Coherent_Asteroid_Mining_Crystal_Type_A_II
 + 9.04977375566 x_Coherent_Asteroid_Mining_Crystal_Type_B_II
 + 9.47867298578 x_Complex_Asteroid_Mining_Crystal_Type_A_II
 + 18.9573459716 x_Complex_Asteroid_Mining_Crystal_Type_B_II
 + 11.8483412322 x_Mercoxit_Asteroid_Mining_Crystal_Type_A_II
 + 4.52488687783 x_Simple_Asteroid_Mining_Crystal_Type_A_II
 + 9.04977375566 x_Simple_Asteroid_Mining_Crystal_Type_B_II
 + 7.10900473934 x_Variegated_Asteroid_Mining_Crystal_Type_A_II
 + 14.2180094787 x_Variegated_Asteroid_Mining_Crystal_Type_B_II <= 1122

_C21: x_Medium_Asteroid_Ore_Compressor_I <= 0

_C22: x_Covert_Cynosural_Field_Generator_I <= 0

_C23: x_Drone_Link_Augmentor_I <= 23

_C24: x_Modulated_Deep_Core_Miner_II <= 0

_C25: x_Simple_Asteroid_Mining_Crystal_Type_B_II <= 946

_C26: x_R.A.M.__Energy_Tech <= 0

_C27: x_R.A.M.__Electronics <= 0

VARIABLES
0 <= x_Bastion_Module_I Integer
0 <= x_Coherent_Asteroid_Mining_Crystal_Type_A_I Integer
0 <= x_Coherent_Asteroid_Mining_Crystal_Type_A_II Integer
0 <= x_Coherent_Asteroid_Mining_Crystal_Type_B_I Integer
0 <= x_Coherent_Asteroid_Mining_Crystal_Type_B_II Integer
0 <= x_Complex_Asteroid_Mining_Crystal_Type_A_I Integer
0 <= x_Complex_Asteroid_Mining_Crystal_Type_A_II Integer
0 <= x_Complex_Asteroid_Mining_Crystal_Type_B_I Integer
0 <= x_Complex_Asteroid_Mining_Crystal_Type_B_II Integer
0 <= x_Covert_Cynosural_Field_Generator_I Integer
0 <= x_Deep_Core_Mining_Laser_I Integer
0 <= x_Defender_Launcher_I Integer
0 <= x_Drone_Link_Augmentor_I Integer
0 <= x_Drone_Link_Augmentor_II Integer
0 <= x_Gas_Cloud_Harvester_I Integer
0 <= x_Gas_Cloud_Harvester_II Integer
0 <= x_Industrial_Cynosural_Field_Generator Integer
0 <= x_Interdiction_Sphere_Launcher_I Integer
0 <= x_Large_Asteroid_Ore_Compressor_I Integer
0 <= x_Medium_Asteroid_Ore_Compressor_I Integer
0 <= x_Mercoxit_Asteroid_Mining_Crystal_Type_A_I Integer
0 <= x_Mercoxit_Asteroid_Mining_Crystal_Type_A_II Integer
0 <= x_Mercoxit_Asteroid_Mining_Crystal_Type_B_I Integer
0 <= x_Modulated_Deep_Core_Miner_II Integer
0 <= x_R.A.M.__Electronics Integer
0 <= x_R.A.M.__Energy_Tech Integer
0 <= x_Simple_Asteroid_Mining_Crystal_Type_A_II Integer
0 <= x_Simple_Asteroid_Mining_Crystal_Type_B_I Integer
0 <= x_Simple_Asteroid_Mining_Crystal_Type_B_II Integer
0 <= x_Small_Tractor_Beam_I Integer
0 <= x_Variegated_Asteroid_Mining_Crystal_Type_A_I Integer
0 <= x_Variegated_Asteroid_Mining_Crystal_Type_A_II Integer
0 <= x_Variegated_Asteroid_Mining_Crystal_Type_B_I Integer
0 <= x_Variegated_Asteroid_Mining_Crystal_Type_B_II Integer
