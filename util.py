from HTMLParser import HTMLParser


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def add_to_data(self, url):
        url = ' ' + url + ' '
        self.fed.append(url)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    self.add_to_data(attr[1])
                    # self.fed.append(url)
        elif tag == 'img':
            for attr in attrs:
                if attr[0] == 'src':
                    self.add_to_data(attr[1])
        elif tag == 'br':
            self.add_to_data('\n')

    def handle_data(self, data):
        self.fed.append(data)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def split_text_to_chanks(text, size, result=None):
    result = result or []
    max_size = size
    if len(text) <= size:
        result.append(text)
        return result

    while text[size:size + 2] != '. ' and size > 3500:
        size = size - 1
    result.append(text[0:size + 2])
    rest = text[size + 2:]
    if len(rest) <= max_size:
        result.append(rest)
        return result
    else:
        return split_text_to_chanks(rest, max_size, result)
