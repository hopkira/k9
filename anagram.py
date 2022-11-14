import random
import sys

words = [["actors","costar","castor"],["actress","casters","recasts"],["airmen","marine","remain"],["antler","learnt","rental"],["arches","chaser","search"],["arrest","rarest","raters","starer"],["artist","strait","traits"],["ascent","secant","stance"],["asleep","elapse","please"],["assert","asters","stares"],["barely","barley","bleary"],["bleats","stable","tables"],["bluest","bluets","bustle","sublet","subtle"],["caller","cellar","recall"],["canter","nectar","recant","trance"],["carets","caters","caster","crates","reacts"],["corset","escort","sector"],["danger","gander","garden","ranged"],["dater","rated","trade","tread"],["daters","trades","treads","stared"],["dearth","hatred","thread"],["deigns","design","signed","singed"],["deltas","lasted","slated"],["denter","rented","tender"],["desert","deters","rested"],["detail","dilate","tailed"],["detour","routed","toured"],["diaper","paired","repaid"],["direst","driest","stride"],["doters","sorted","stored"],["drapes","padres","parsed","rasped","spared"],["duster","rudest","rusted"],["earned","endear","neared"],["emoter","meteor","remote"],["endive","envied","veined"],["enlist","inlets","listen","silent","tinsel"],["enters","nester","resent","tenser"],["esprit","priest","sprite","stripe"],["filets","itself","stifle"],["filter","lifter","trifle"],["forest","fortes","foster","softer"],["gilder","girdle","glider"],["ideals","ladies","sailed"],["lament","mantel","mantle","mental"],["lapse","leaps","pales","peals","sepal"],["lemons","melons","solemn"],["lisper","perils","pliers"],["lister","liters","litres","relist","tilers"],["livers","silver","sliver"],["looped","poodle","pooled"],["marines","remains","seminar"],["master","stream","tamers"],["merits","mister","miters","mitres","remits"],["naive","ravine","vainer"],["observe","obverse","verbose"],["palest","pastel","petals","plates","pleats"],["paltry","partly","raptly"],["parley","pearly","player","replay"],["parses","passer","spares","sparse","spears"],["pintos","piston","pitons","points"],["rashes","shares","shears"],["reigns","resign","signer","singer"],["rescue","recuse","secure"],["resort","roster","sorter"],["retests","setter","street","tester"],["retrain","terrain","trainer"],["seated","sedate","teased"],["skated","staked","tasked"],["slates","steals","tassel"],["taster","tetras","treats"],["whiter","wither","writhe"]]

def shuffle_word(word:str) -> str:
    word = list(word)
    random.shuffle(word)
    return "".join(word)

def choose_answers(words:list) -> list:
    return words[random.randint(0,len(words)-1)]

def enter_answers(test, answer_list) -> bool:
    global score
    answers = []
    num_answers = len(answer_list)
    for num in range(1, num_answers+1):
        request_str = "Give me an anagram of "+test+" ("+str(num)+" of "+str(num_answers)+") -> "
        answer = input(request_str)
        if answer in answer_list:
            if answer in answers:
                print("Duplicate entry")
                return False
            else:
                score += (6 * num)
                answers.append(answer)
                continue
        else:
            print("Not a valid anagram")
            return False
    return True

score = 0

while True:
    answer_list = choose_answers(words)
    print(answer_list)
    test = shuffle_word(answer_list[0])
    if enter_answers(test, answer_list):
        print("Well done!")
    else:
        print("Game over, score:", score)
        sys.exit(0)
