from rdkit import Chem

mol = Chem.MolFromMolFile("chiral.mol")
Chem.AssignStereochemistry(mol, flagPossibleStereoCenters=True, force=True)

f_idx = [a.GetIdx() for a in mol.GetAtoms() if a.GetSymbol() == 'F'][0]
br_idx = [a.GetIdx() for a in mol.GetAtoms() if a.GetSymbol() == 'Br'][0]

path = Chem.GetShortestPath(mol, f_idx, br_idx)
path_atoms = [mol.GetAtomWithIdx(idx) for idx in path]

print("Path length:", len(path))
rs = []
for a in path_atoms:
    if a.HasProp('_CIPCode'):
        rs.append(a.GetProp('_CIPCode'))
    else:
        rs.append('-')
        
print("Stereo along path:", "".join(rs))
