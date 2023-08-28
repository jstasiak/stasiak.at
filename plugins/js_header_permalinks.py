from pelican import readers
from pelican.readers import PelicanHTMLTranslator
from docutils import nodes

class HTMLTranslator(PelicanHTMLTranslator):
    def visit_title(self, node: nodes.title) -> None:
        PelicanHTMLTranslator.visit_title(self, node)
        header_id = self.header_id(node)
        if header_id:
            self.body.append(f'<a class="header" href="#{header_id}">')

    def depart_title(self, node: nodes.title) -> None:
        header_id = self.header_id(node)
        if header_id:
            self.body.append('</a>')
        PelicanHTMLTranslator.depart_title(self, node)

    def header_id(self, node: nodes.title) -> str | None:
        parent = node.parent
        close_tag = self.context[-1]
        if not (
            isinstance(parent, nodes.section)
            and parent.hasattr('ids')
            and parent['ids']
            and close_tag.startswith('</h')
        ):
            return None
        return parent['ids'][0]


def register():
    readers.PelicanHTMLTranslator = HTMLTranslator
