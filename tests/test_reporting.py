from insightguard.reporting.report_generator import generate_report, generate_report_bytes


def test_report_bytes_escape_markup_and_create_valid_pdf():
    pdf = generate_report_bytes(
        'Title <script> & review',
        'Summary with <b>literal markup</b> & symbols',
        ['Evidence <item> & recommendation'],
    )

    assert pdf.startswith(b'%PDF-')
    assert len(pdf) > 500


def test_report_file_api_remains_available(tmp_path):
    output = tmp_path / 'reports' / 'summary.pdf'

    returned_path = generate_report(output, 'Summary', 'A short report', ['Review findings'])

    assert returned_path == str(output)
    assert output.read_bytes().startswith(b'%PDF-')