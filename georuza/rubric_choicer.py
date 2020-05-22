import json
import readchar

from georuza import settings


def main():
    marked_rubrics = []
    with open(settings.FILES_DIR / '2gis-rubrics-data.json') as f:
        rubrics = json.loads(f.read())

    for rub in rubrics:
        print(rub['title'])
        c = readchar.readchar()
        if c == 'y' or c == 'н':
            marked_rubrics.append(rub)
            print('Ok')
            continue
        if c == 's' or c == 'ы':
            break

    with open(settings.FILES_DIR / 'rubrics-choice-1.json', 'w') as f:
        json.dump(marked_rubrics, f, ensure_ascii=False)
main()