from html.parser import HTMLParser
from pathlib import Path
import csv
import pytest
from research.make_sheets import render


class Reader(HTMLParser):
    def __init__(self):
        super().__init__();self.current=None;self.data={}
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'data-case' in attrs:
            self.current=attrs['data-case'];self.data[self.current]=[]
    def handle_data(self,data):
        if self.current:self.data[self.current].append(data)


def test_every_reviewed_value_survives_printable_generation(tmp_path):
    source=Path('research/inputs/judged_cases_v11.csv')
    target=tmp_path/'packet.html'
    render(source,target)
    reader=Reader();reader.feed(target.read_text(encoding='utf-8'))
    rows=list(csv.DictReader(source.open(encoding='utf-8-sig')))
    assert len(reader.data)==40
    for row in rows:
        text=' '.join(reader.data[row['case_id']])
        assert text.count('₱250,000')==1
        for key,value in row.items():
            if value.strip() and key not in ('case_id','amount_granted'):
                assert value in text,(row['case_id'],key)
    with pytest.raises(ValueError):render(source,target)
