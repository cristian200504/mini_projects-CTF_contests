import re

verilog = """
  assign _111_ = ~character[1];
  assign _121_ = ~character[2];
  assign _132_ = ~character[3];
  assign _142_ = ~character[6];
  assign _153_ = ~character[0];
  assign _163_ = ~character[4];
  assign _174_ = ~character[5];
  assign _184_ = ~s[0];
  assign _195_ = ~s[1];
  assign _206_ = ~s[2];
  assign _217_ = ~s[4];
  assign _222_ = ~s[3];
  assign _223_ = ~(_184_ | _195_);
  assign _224_ = ~(s[0] & s[1]);
  assign _225_ = ~(s[2] & s[3]);
  assign _226_ = ~_225_;
  assign _227_ = ~(_224_ | _225_);
  assign _228_ = ~(s[4] & _227_);
  assign found_flag = ~_228_;
  assign _229_ = ~(s[4] | _227_);
  assign _230_ = ~(found_flag | _229_);
  assign _231_ = ~_230_;
  assign _232_ = ~(s[2] | s[3]);
  assign _233_ = ~_232_;
  assign _234_ = ~(s[0] | s[1]);
  assign _235_ = ~(_184_ & _195_);
  assign _236_ = ~(_232_ & _234_);
  assign _237_ = ~(s[4] & _236_);
  assign _238_ = ~_237_;
  assign _239_ = ~(_229_ | _238_);
  assign _240_ = ~(_142_ | character[4]);
  assign _241_ = ~(character[6] & _163_);
  assign _242_ = ~(_174_ | _241_);
  assign _243_ = ~(character[5] & _240_);
  assign _244_ = ~(_121_ | character[3]);
  assign _245_ = ~(character[2] & _132_);
  assign _246_ = ~(_111_ | character[0]);
  assign _247_ = ~(character[1] & _153_);
  assign _248_ = ~(_244_ & _246_);
  assign _249_ = ~(_243_ | _248_);
  assign _250_ = ~(_239_ & _249_);
  assign _251_ = ~(s[2] | _222_);
  assign _252_ = ~(_206_ & s[3]);
  assign _253_ = ~(_223_ & _251_);
  assign _254_ = ~(s[0] | _195_);
  assign _255_ = ~(_184_ & s[1]);
  assign _256_ = ~(_232_ & _254_);
  assign _257_ = ~(_253_ & _256_);
  assign _258_ = ~(_235_ | _252_);
  assign _259_ = ~(_234_ & _251_);
  assign _260_ = ~(_206_ | s[3]);
  assign _261_ = ~(s[2] & _222_);
  assign _262_ = ~(s[2] & _223_);
  assign _263_ = ~_262_;
  assign _264_ = ~(_224_ | _261_);
  assign _265_ = ~(_223_ & _260_);
  assign _266_ = ~(s[4] | _264_);
  assign _267_ = ~(s[4] & _259_);
  assign _268_ = ~(_257_ | _267_);
  assign _269_ = ~(_266_ | _268_);
  assign _270_ = ~(character[2] | character[3]);
  assign _271_ = ~(_111_ | _153_);
  assign _272_ = ~(character[1] & character[0]);
  assign _273_ = ~(_270_ & _271_);
  assign _274_ = ~(_243_ | _273_);
  assign _275_ = ~(_269_ & _274_);
  assign _276_ = ~(s[4] | s[3]);
  assign _277_ = ~_276_;
  assign _278_ = ~(s[0] & _195_);
  assign _279_ = ~_278_;
  assign _280_ = ~(s[4] | _278_);
  assign _281_ = ~_280_;
  assign _282_ = ~(_265_ & _281_);
  assign _283_ = ~(_277_ & _282_);
  assign _284_ = ~(character[6] & character[4]);
  assign _285_ = ~(character[5] | _284_);
  assign _286_ = ~(_121_ | _132_);
  assign _287_ = ~(character[2] & character[3]);
  assign _288_ = ~(_285_ & _286_);
  assign _001_ = ~(_283_ | _288_);
  assign _002_ = ~(_271_ & _001_);
  assign _003_ = ~(_275_ & _002_);
  assign _004_ = ~_003_;
  assign _005_ = ~(_255_ | _261_);
  assign _006_ = ~_005_;
  assign _007_ = ~(_217_ & _005_);
  assign _008_ = ~(_217_ | _278_);
  assign _009_ = ~(s[4] & _279_);
  assign _010_ = ~(_232_ & _008_);
  assign _011_ = ~(_007_ & _010_);
  assign _012_ = ~(_163_ | _174_);
  assign _013_ = ~(character[4] & character[5]);
  assign _014_ = ~(character[6] | _013_);
  assign _015_ = ~(_142_ & _012_);
  assign _016_ = ~(character[1] | _153_);
  assign _017_ = ~(_111_ & character[0]);
  assign _018_ = ~(_270_ & _016_);
  assign _019_ = ~(_015_ | _018_);
  assign _020_ = ~(_011_ & _019_);
  assign _021_ = ~(_225_ | _255_);
  assign _022_ = ~(s[4] | _021_);
  assign _023_ = ~(_235_ | _261_);
  assign _024_ = ~(_234_ & _260_);
  assign _025_ = ~(_217_ | _023_);
  assign _026_ = ~(_022_ | _025_);
  assign _027_ = ~(_273_ | _015_);
  assign _028_ = ~(_026_ & _027_);
  assign _029_ = ~(_020_ & _028_);
  assign _030_ = ~(_003_ | _029_);
  assign _031_ = ~(_250_ & _030_);
  assign _032_ = ~(_230_ & _031_);
  assign _033_ = ~(_225_ | _235_);
  assign _034_ = ~_033_;
  assign _035_ = ~(s[4] & _033_);
  assign _036_ = ~_035_;
  assign _037_ = ~(s[4] | _259_);
  assign _038_ = ~(_217_ & _258_);
  assign _039_ = ~(_035_ & _038_);
  assign _040_ = ~(_036_ | _037_);
  assign _041_ = ~(_121_ & character[3]);
  assign _042_ = ~(_272_ | _041_);
  assign _043_ = ~_042_;
  assign _044_ = ~(_243_ | _043_);
  assign _045_ = ~(_242_ & _042_);
  assign _046_ = ~(_040_ | _045_);
  assign _047_ = ~(_039_ & _044_);
  assign _048_ = ~(s[4] & _021_);
  assign _049_ = ~(_142_ | _013_);
  assign _050_ = ~(character[6] & _012_);
  assign _051_ = ~(_287_ | _017_);
  assign _052_ = ~(_049_ & _051_);
  assign _053_ = ~(_048_ | _052_);
  assign _054_ = ~_053_;
  assign _055_ = ~(_225_ | _009_);
  assign _056_ = ~(_226_ & _008_);
  assign _057_ = ~(_245_ | _017_);
  assign _058_ = ~(_244_ & _016_);
  assign _059_ = ~(_015_ | _058_);
  assign _060_ = ~(_014_ & _057_);
  assign _061_ = ~(_056_ | _060_);
  assign _062_ = ~(_055_ & _059_);
  assign _063_ = ~(_053_ | _061_);
  assign _064_ = ~(_054_ & _062_);
  assign _065_ = ~(_046_ | _064_);
  assign _066_ = ~(_047_ & _063_);
  assign _067_ = ~(_231_ | _065_);
  assign _068_ = ~(s[4] | _253_);
  assign _069_ = ~_068_;
  assign _070_ = ~(_261_ | _009_);
  assign _071_ = ~(_260_ & _008_);
  assign _072_ = ~(_068_ | _070_);
  assign _073_ = ~(_069_ & _071_);
  assign _074_ = ~(_247_ | _287_);
  assign _075_ = ~(_242_ & _074_);
  assign _076_ = ~(_072_ | _075_);
  assign _077_ = ~(_230_ & _076_);
  assign _078_ = ~(_217_ | _006_);
  assign _079_ = ~(s[4] & _005_);
  assign _080_ = ~(_245_ | _272_);
  assign _081_ = ~(_244_ & _271_);
  assign _082_ = ~(_015_ | _081_);
  assign _083_ = ~(_014_ & _080_);
  assign _084_ = ~(_079_ | _083_);
  assign _085_ = ~(_078_ & _082_);
  assign _086_ = ~(_224_ | _233_);
  assign _087_ = ~(_223_ & _232_);
  assign _088_ = ~(_217_ | _041_);
  assign _089_ = ~(_086_ & _088_);
  assign _090_ = ~(_242_ & _016_);
  assign _091_ = ~(_089_ | _090_);
  assign _092_ = ~(_243_ | _089_);
  assign _093_ = ~(_016_ & _092_);
  assign _094_ = ~(_084_ | _091_);
  assign _095_ = ~(_085_ & _093_);
  assign _096_ = ~(character[1] | character[0]);
  assign _097_ = ~(_242_ & _096_);
  assign _098_ = ~_097_;
  assign _099_ = ~(_252_ | _041_);
  assign _100_ = ~(_251_ & _008_);
  assign _101_ = ~(_041_ | _100_);
  assign _102_ = ~(_008_ & _099_);
  assign _103_ = ~(_097_ | _102_);
  assign _104_ = ~(_098_ & _101_);
  assign _105_ = ~(_252_ | _255_);
  assign _106_ = ~(_251_ & _254_);
  assign _107_ = ~(s[4] & _105_);
  assign _108_ = ~_107_;
  assign _109_ = ~(_243_ | _058_);
  assign _110_ = ~(_242_ & _057_);
  assign _112_ = ~(_107_ | _110_);
  assign _113_ = ~(_108_ & _109_);
  assign _114_ = ~(_103_ | _112_);
  assign _115_ = ~(_104_ & _113_);
  assign _116_ = ~(_095_ | _115_);
  assign _117_ = ~(_094_ & _114_);
  assign _118_ = ~(_077_ & _116_);
  assign _119_ = ~(_067_ | _118_);
  assign _289_4 = ~(_032_ & _119_);
  assign _120_ = ~(s[3] & _262_);
  assign _122_ = ~(_265_ & _120_);
  assign _123_ = ~(_046_ | _076_);
  assign _124_ = ~(_004_ & _123_);
  assign _125_ = ~(_122_ & _124_);
  assign _126_ = ~(s[4] | _034_);
  assign _127_ = ~(_245_ | _097_);
  assign _128_ = ~(_126_ & _127_);
  assign _129_ = ~_128_;
  assign _130_ = ~(s[4] | _106_);
  assign _131_ = ~(_243_ | _018_);
  assign _133_ = ~(_130_ & _131_);
  assign _134_ = ~(_028_ & _133_);
  assign _135_ = ~(_122_ & _134_);
  assign _136_ = ~(_064_ | _115_);
  assign _137_ = ~(_135_ & _136_);
  assign _138_ = ~(_129_ | _137_);
  assign _289_3 = ~(_125_ & _138_);
  assign _139_ = ~(s[2] | _223_);
  assign _140_ = ~(_263_ | _139_);
  assign _141_ = ~(s[4] | _024_);
  assign _143_ = ~_141_;
  assign _144_ = ~(_018_ | _143_);
  assign _145_ = ~(s[4] | _233_);
  assign _146_ = ~(_042_ & _145_);
  assign _147_ = ~(_224_ | _146_);
  assign _148_ = ~(_144_ | _147_);
  assign _149_ = ~(_050_ | _148_);
  assign _150_ = ~(_076_ | _149_);
  assign _151_ = ~(_030_ & _150_);
  assign _152_ = ~(_140_ & _151_);
  assign _154_ = ~(_260_ & _280_);
  assign _155_ = ~(_049_ & _057_);
  assign _156_ = ~(_154_ | _155_);
  assign _157_ = ~_156_;
  assign _158_ = ~(_095_ | _156_);
  assign _159_ = ~(_128_ & _158_);
  assign _160_ = ~(_067_ | _159_);
  assign _289_2 = ~(_152_ & _160_);
  assign _161_ = ~(_255_ & _278_);
  assign _162_ = ~(_240_ & _074_);
  assign _164_ = ~(character[5] | _162_);
  assign _165_ = ~_164_;
  assign _166_ = ~(s[0] & _145_);
  assign _167_ = ~(_165_ | _166_);
  assign _168_ = ~(_255_ | _273_);
  assign _169_ = ~_168_;
  assign _170_ = ~(_285_ & _145_);
  assign _171_ = ~_170_;
  assign _172_ = ~(_169_ | _170_);
  assign _173_ = ~(_168_ & _171_);
  assign _175_ = ~(_020_ & _173_);
  assign _176_ = ~(_167_ | _175_);
  assign _177_ = ~(_004_ & _176_);
  assign _178_ = ~(_161_ & _177_);
  assign _179_ = ~(_085_ & _157_);
  assign _180_ = ~_179_;
  assign _181_ = ~(_077_ & _180_);
  assign _182_ = ~(_137_ | _181_);
  assign _289_1 = ~(_178_ & _182_);
  assign _183_ = ~(_149_ | _172_);
  assign _185_ = ~(_250_ & _157_);
  assign _186_ = ~(_117_ | _185_);
  assign _187_ = ~(_029_ | _066_);
  assign _188_ = ~(_186_ & _187_);
  assign _189_ = ~(_003_ | _188_);
  assign _190_ = ~(_183_ & _189_);
  assign _191_ = ~(_184_ & _190_);
  assign _192_ = ~(character[5] & s[0]);
  assign _193_ = ~_192_;
  assign _194_ = ~(_162_ | _193_);
  assign _196_ = ~(_073_ & _194_);
  assign _197_ = ~(_079_ & _087_);
  assign _198_ = ~(_141_ | _145_);
  assign _199_ = ~(s[0] | _198_);
  assign _200_ = ~(s[3] & _008_);
  assign _201_ = ~(_011_ | _026_);
  assign _202_ = ~(_283_ & _201_);
  assign _203_ = ~(_039_ | _202_);
  assign _204_ = ~(_107_ & _200_);
  assign _205_ = ~(_048_ & _154_);
  assign _207_ = ~(_204_ | _205_);
  assign _208_ = ~(_239_ | _197_);
  assign _209_ = ~(_207_ & _208_);
  assign _210_ = ~(_199_ | _209_);
  assign _211_ = ~(_203_ & _210_);
  assign _212_ = ~(_269_ | _211_);
  assign _213_ = ~(_165_ | _212_);
  assign _214_ = ~(_130_ & _164_);
  assign _215_ = ~(_196_ & _214_);
  assign _216_ = ~(_126_ & _164_);
  assign _218_ = ~(_133_ & _216_);
  assign _219_ = ~(_215_ | _218_);
  assign _220_ = ~(_128_ & _219_);
  assign _221_ = ~(_213_ | _220_);
  assign _289_0 = ~(_191_ & _221_);
"""

def compile_to_python(v_code):
    lines = v_code.strip().split('\n')
    py_lines = []
    py_lines.append("def next_state(state, char):")
    py_lines.append("    s = [(state >> i) & 1 for i in range(5)]")
    py_lines.append("    character = [(char >> i) & 1 for i in range(7)]")
    
    for line in lines:
        line = line.strip()
        if not line: continue
        if line.startswith("assign "):
            # e.g. assign _111_ = ~character[1];
            # assign _289_[4] = ...
            m = re.match(r'assign\s+([a-zA-Z0-9_\[\]]+)\s*=\s*(.*);', line)
            if m:
                lhs = m.group(1)
                rhs = m.group(2)
                
                lhs = lhs.replace('[', '_').replace(']', '')
                rhs = rhs.replace('~', ' 1 ^ ')
                rhs = rhs.replace('|', ' | ')
                rhs = rhs.replace('&', ' & ')
                
                # special handling for s[0], character[0]
                rhs = re.sub(r's\[(\d)\]', r's[\1]', rhs)
                rhs = re.sub(r'character\[(\d)\]', r'character[\1]', rhs)
                
                py_lines.append(f"    {lhs} = ({rhs}) & 1")
    
    py_lines.append("    return _289_0 | (_289_1 << 1) | (_289_2 << 2) | (_289_3 << 3) | (_289_4 << 4)")
    
    return "\n".join(py_lines)

with open("sim.py", "w") as f:
    f.write(compile_to_python(verilog))
    f.write("""
def solve():
    path = []
    current_state = 0
    flag = ""
    while current_state != 31:
        found = False
        for c in range(32, 127):
            ns = next_state(current_state, c)
            if ns == current_state + 1:
                flag += chr(c)
                current_state = ns
                found = True
                break
        if not found:
            print("Stuck at state", current_state)
            break
    print("Flag:", flag)

solve()
""")
