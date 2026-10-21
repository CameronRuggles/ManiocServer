/* === OnionHost OS ===
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "OnionHostPhraseViewStep.h"

#include "GlobalStorage.h"
#include "JobQueue.h"
#include "utils/Logger.h"

#include <QFile>
#include <QGridLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QRandomGenerator>
#include <QRegularExpression>
#include <QSet>
#include <QStackedWidget>
#include <QVBoxLayout>

#include <algorithm>
#include <cerrno>
#include <cstring>
#include <sys/random.h>

CALAMARES_PLUGIN_FACTORY_DEFINITION( OnionHostPhraseViewStepFactory,
                                     registerPlugin< OnionHostPhraseViewStep >(); )

namespace
{

// Calamares::String::obscure (an involution): characters <= U+0021
// pass through, others map to U+1001F - codepoint. Used both to
// store the phrase in GlobalStorage in the form the partition
// chain expects, and to un-obscure it for display.
QString
obscure( const QString& in )
{
    QString out;
    out.reserve( in.size() );
    for ( const QChar c : in )
    {
        const ushort u = c.unicode();
        out.append( u <= 0x21 ? c : QChar( 0x1001F - u ) );
    }
    return out;
}

// --- Phrase generation (DESIGN-v3 A19.1 entropy gate) -------------
// Port of /usr/lib/onionhost/phrasegen.py (the wizard and the
// re-key tool use the Python implementation; the algorithm is
// identical): bytes from getrandom(2) with flags=0 - the call
// BLOCKS until the kernel CSPRNG is seeded - and rejection
// sampling: 13-bit candidates (7776 < 2^13) masked from fresh
// random bytes, candidates >= 7776 discarded. No modulo anywhere.

const QString kWordlistPath
    = QStringLiteral( "/usr/share/onionhost/eff-large-wordlist.txt" );

bool
loadWords( QStringList& words )
{
    QFile f( kWordlistPath );
    if ( !f.open( QIODevice::ReadOnly | QIODevice::Text ) )
    {
        return false;
    }
    const QString all = QString::fromUtf8( f.readAll() );
    for ( const QString& line : all.split( QLatin1Char( '\n' ) ) )
    {
        const QStringList parts
            = line.split( QRegularExpression( QStringLiteral( "\\s+" ) ),
                          Qt::SkipEmptyParts );
        if ( !parts.isEmpty() )
        {
            words.append( parts.last() );
        }
    }
    if ( words.size() != 7776 )
    {
        return false;
    }
    QSet< QString > unique( words.begin(), words.end() );
    return unique.size() == 7776;
}

int
randBelow( int n )
{
    // nbits = bit length of (n-1): for n = 7776, 13 bits.
    const int nbits
        = 32 - __builtin_clz( static_cast< unsigned >( n - 1 ) );
    const int nbytes = ( nbits + 7 ) / 8;
    const unsigned mask = ( 1u << nbits ) - 1;
    unsigned char buf[ 4 ];
    for ( ;; )
    {
        size_t got = 0;
        while ( got < static_cast< size_t >( nbytes ) )
        {
            const ssize_t r
                = getrandom( buf + got, nbytes - got, 0 );
            if ( r < 0 )
            {
                if ( errno == EINTR )
                {
                    continue;
                }
                return -1;
            }
            got += static_cast< size_t >( r );
        }
        unsigned candidate = 0;
        for ( int i = 0; i < nbytes; i++ )
        {
            candidate = ( candidate << 8 ) | buf[ i ];
        }
        candidate &= mask;
        if ( candidate < static_cast< unsigned >( n ) )
        {
            return static_cast< int >( candidate );
        }
    }
}

bool
generatePhrase( const QStringList& words, int count, QString& out )
{
    QStringList picked;
    for ( int i = 0; i < count; i++ )
    {
        const int idx = randBelow( words.size() );
        if ( idx < 0 )
        {
            return false;
        }
        picked.append( words[ idx ] );
    }
    out = picked.join( QLatin1Char( ' ' ) );
    return true;
}

QLabel*
makeTitle( const QString& text )
{
    auto* label = new QLabel( text );
    QFont f = label->font();
    f.setPointSize( 22 );
    f.setBold( true );
    label->setFont( f );
    return label;
}

QLabel*
makeBody( const QString& text )
{
    auto* label = new QLabel( text );
    label->setWordWrap( true );
    QFont f = label->font();
    f.setPointSize( 12 );
    label->setFont( f );
    return label;
}

QPushButton*
makePrimaryButton( const QString& text )
{
    auto* button = new QPushButton( text );
    button->setStyleSheet(
        QStringLiteral( "QPushButton { background-color: #2d6a2d; color: white;"
                        " font-weight: bold; font-size: 13pt; padding: 10px 18px;"
                        " border-radius: 6px; }"
                        "QPushButton:hover { background-color: #357a35; }" ) );
    return button;
}

}  // namespace

OnionHostPhraseViewStep::OnionHostPhraseViewStep( QObject* parent )
    : Calamares::ViewStep( parent )
{
    buildUi();
    emit nextStatusChanged( true );
}

OnionHostPhraseViewStep::~OnionHostPhraseViewStep()
{
    if ( m_widget && m_widget->parent() == nullptr )
    {
        m_widget->deleteLater();
    }
}

QString
OnionHostPhraseViewStep::prettyName() const
{
    return tr( "Disk passphrase", "@label" );
}

QWidget*
OnionHostPhraseViewStep::widget()
{
    return m_widget;
}

bool
OnionHostPhraseViewStep::isNextEnabled() const
{
    return m_stage == Stage::Show || m_stage == Stage::Done;
}

bool
OnionHostPhraseViewStep::isBackEnabled() const
{
    return true;
}

bool
OnionHostPhraseViewStep::isAtBeginning() const
{
    return m_stage == Stage::Show || m_stage == Stage::Error;
}

bool
OnionHostPhraseViewStep::isAtEnd() const
{
    return m_stage == Stage::Done;
}

Calamares::JobList
OnionHostPhraseViewStep::jobs() const
{
    return Calamares::JobList();
}

void
OnionHostPhraseViewStep::buildUi()
{
    m_widget = new QWidget;
    auto* mainLayout = new QVBoxLayout( m_widget );
    mainLayout->setContentsMargins( 30, 22, 30, 10 );
    auto* title = makeTitle( tr( "Your disk passphrase", "@title" ) );
    mainLayout->addWidget( title );
    m_stack = new QStackedWidget;
    mainLayout->addWidget( m_stack );
    mainLayout->addStretch();

    // --- Show page -------------------------------------------------
    auto* showPage = new QWidget;
    auto* showLayout = new QVBoxLayout( showPage );
    showLayout->setContentsMargins( 0, 6, 0, 0 );
    showLayout->addWidget( makeBody(
        tr( "This computer made up a passphrase of 7 words for you. "
            "It locks the whole disk.\n\n"
            "Write the 7 words on a piece of paper, by hand, in "
            "order. Keep the paper somewhere safe.\n\n"
            "You will type this passphrase every time the computer "
            "starts. It is the only key there is - there is no "
            "spare and no other way in. If the paper is lost, the "
            "computer, the website and even the backups are gone "
            "for good.",
            "@body" ) ) );
    m_chips = new QWidget;
    m_chips->setLayout( new QGridLayout( m_chips ) );
    showLayout->addWidget( m_chips );
    auto* writtenButton = makePrimaryButton(
        tr( "I have written them down", "@button" ) );
    connect( writtenButton, &QPushButton::clicked, this, [ this ]() {
        if ( m_stage == Stage::Show )
        {
            next();
        }
    } );
    auto* buttonRow = new QHBoxLayout;
    buttonRow->addWidget( writtenButton );
    buttonRow->addStretch();
    showLayout->addLayout( buttonRow );
    showLayout->addStretch();
    m_stack->addWidget( showPage );

    // --- Verify page ------------------------------------------------
    auto* verifyPage = new QWidget;
    auto* verifyLayout = new QVBoxLayout( verifyPage );
    verifyLayout->setContentsMargins( 0, 6, 0, 0 );
    verifyLayout->addWidget( makeBody(
        tr( "Now check your paper. Type these words exactly as you "
            "wrote them down:",
            "@body" ) ) );
    for ( int i = 0; i < 3; i++ )
    {
        auto* row = new QHBoxLayout;
        m_posLabels[ i ] = new QLabel;
        QFont lf = m_posLabels[ i ]->font();
        lf.setPointSize( 13 );
        m_posLabels[ i ]->setFont( lf );
        m_posLabels[ i ]->setMinimumWidth( 190 );
        row->addWidget( m_posLabels[ i ] );
        m_edits[ i ] = new QLineEdit;
        m_edits[ i ]->setMinimumWidth( 260 );
        QFont ef;
        ef.setFamily( QStringLiteral( "monospace" ) );
        ef.setPointSize( 14 );
        m_edits[ i ]->setFont( ef );
        connect( m_edits[ i ], &QLineEdit::textChanged, this,
                 [ this ]() { checkVerify(); } );
        row->addWidget( m_edits[ i ] );
        row->addStretch();
        verifyLayout->addLayout( row );
    }
    m_hint = new QLabel;
    m_hint->setStyleSheet( QStringLiteral( "color: #b00020;" ) );
    m_hint->setWordWrap( true );
    verifyLayout->addWidget( m_hint );
    verifyLayout->addWidget( makeBody(
        tr( "If a word does not match, look at your paper again. If "
            "you copied a word wrongly, fix the paper - the computer "
            "will only accept the words on the screen before.",
            "@body" ) ) );
    auto* againButton = new QPushButton(
        tr( "Show the words again", "@button" ) );
    connect( againButton, &QPushButton::clicked, this,
             [ this ]() { showStage( Stage::Show ); } );
    auto* againRow = new QHBoxLayout;
    againRow->addWidget( againButton );
    againRow->addStretch();
    verifyLayout->addLayout( againRow );
    verifyLayout->addStretch();
    m_stack->addWidget( verifyPage );

    // --- Done page ---------------------------------------------------
    auto* donePage = new QWidget;
    auto* doneLayout = new QVBoxLayout( donePage );
    doneLayout->setContentsMargins( 0, 6, 0, 0 );
    auto* doneTitle = makeTitle( tr( "Your paper copy is correct.",
                                     "@title" ) );
    doneTitle->setStyleSheet( QStringLiteral( "color: #2d6a2d;" ) );
    doneLayout->addWidget( doneTitle );
    doneLayout->addWidget( makeBody(
        tr( "Press Next. On the partitioning screen, choose "
            "\"Erase disk\". Encryption is switched on for you "
            "automatically, using these same 7 words - there is "
            "nothing to tick and no passphrase to type.",
            "@body" ) ) );
    doneLayout->addStretch();
    m_stack->addWidget( donePage );

    // --- Error page --------------------------------------------------
    auto* errorPage = new QWidget;
    auto* errorLayout = new QVBoxLayout( errorPage );
    errorLayout->setContentsMargins( 0, 6, 0, 0 );
    auto* errorBody = makeBody(
        tr( "Something went wrong while creating your passphrase. "
            "Please go back and try again. If this keeps happening, "
            "do not continue the installation.",
            "@body" ) );
    errorBody->setStyleSheet( QStringLiteral( "color: #b00020;" ) );
    errorLayout->addWidget( errorBody );
    errorLayout->addStretch();
    m_stack->addWidget( errorPage );
}

void
OnionHostPhraseViewStep::rebuildChips()
{
    auto* layout = qobject_cast< QGridLayout* >( m_chips->layout() );
    QLayoutItem* item;
    while ( ( item = layout->takeAt( 0 ) ) != nullptr )
    {
        delete item->widget();
        delete item;
    }
    int n = 0;
    for ( const QString& word : m_words )
    {
        auto* chip = new QLabel( QStringLiteral( "%1. %2" ).arg( n + 1 ).arg( word ) );
        QFont f;
        f.setFamily( QStringLiteral( "monospace" ) );
        f.setPointSize( 16 );
        f.setBold( true );
        chip->setFont( f );
        chip->setStyleSheet( QStringLiteral(
            "QLabel { background-color: #eef3ee; color: #1c2b1c;"
            " border: 1px solid #7a9a7a; border-radius: 6px;"
            " padding: 10px 12px; }" ) );
        layout->addWidget( chip, n / 4, n % 4 );
        n++;
    }
}

void
OnionHostPhraseViewStep::showStage( Stage s )
{
    m_stage = s;
    m_stack->setCurrentIndex( static_cast< int >( s ) );
    emit nextStatusChanged( isNextEnabled() );
}

void
OnionHostPhraseViewStep::onActivate()
{
    auto* gs = Calamares::JobQueue::instance()->globalStorage();
    QString plain;
    if ( gs->contains( QStringLiteral( "onionhostGeneratedPhrase" ) ) )
    {
        // Already generated this session (the user navigated back
        // and forth): keep the SAME phrase, so a paper copy made
        // earlier stays valid.
        plain = obscure( gs->value(
                             QStringLiteral( "onionhostGeneratedPhrase" ) )
                             .toString() );
    }
    else
    {
        // Generate now, in the view step: Calamares 3.3 runs job
        // modules only in the exec phase (ExecutionViewStep is the
        // sole jobs() caller), so a show-phase job cannot do this.
        QStringList words;
        if ( !loadWords( words ) || !generatePhrase( words, 7, plain ) )
        {
            cWarning() << "OnionHostPhrase: phrase generation failed";
            showStage( Stage::Error );
            return;
        }
        const QString obscuredPhrase = obscure( plain );
        gs->insert( QStringLiteral( "luksPassphrase" ), obscuredPhrase );
        gs->insert( QStringLiteral( "onionhostGeneratedPhrase" ),
                    obscuredPhrase );
        cDebug() << "OnionHostPhrase: generated disk phrase";
    }
    m_words = plain.split( QLatin1Char( ' ' ), Qt::SkipEmptyParts );
    if ( m_words.size() != 7 )
    {
        cWarning() << "OnionHostPhrase: generated phrase has"
                   << m_words.size() << "words";
        showStage( Stage::Error );
        return;
    }
    rebuildChips();
    m_positions.clear();
    while ( m_positions.size() < 3 )
    {
        const int p = 1 + static_cast< int >(
                              QRandomGenerator::global()->bounded(
                                  m_words.size() ) );
        if ( !m_positions.contains( p ) )
        {
            m_positions.append( p );
        }
    }
    std::sort( m_positions.begin(), m_positions.end() );
    for ( int i = 0; i < 3; i++ )
    {
        m_posLabels[ i ]->setText(
            tr( "Word number %1:", "@label" ).arg( m_positions[ i ] ) );
        m_edits[ i ]->clear();
    }
    m_hint->clear();
    showStage( Stage::Show );
}

void
OnionHostPhraseViewStep::checkVerify()
{
    if ( m_stage != Stage::Verify )
    {
        return;
    }
    bool anyWrong = false;
    bool allRight = true;
    for ( int i = 0; i < 3; i++ )
    {
        const QString typed = m_edits[ i ]->text().trimmed().toLower();
        const QString want = m_words[ m_positions[ i ] - 1 ].toLower();
        if ( typed.isEmpty() )
        {
            allRight = false;
        }
        else if ( typed != want )
        {
            allRight = false;
            anyWrong = true;
        }
    }
    m_hint->setText( anyWrong
                         ? tr( "A word does not match your paper - "
                               "check the paper and try again.",
                               "@info" )
                         : QString() );
    if ( allRight )
    {
        auto* gs = Calamares::JobQueue::instance()->globalStorage();
        gs->insert( QStringLiteral( "onionhostPhraseVerified" ), 1 );
        showStage( Stage::Done );
    }
}

void
OnionHostPhraseViewStep::next()
{
    if ( m_stage == Stage::Show )
    {
        showStage( Stage::Verify );
        m_edits[ 0 ]->setFocus();
    }
}

void
OnionHostPhraseViewStep::back()
{
    if ( m_stage == Stage::Verify )
    {
        showStage( Stage::Show );
    }
    else if ( m_stage == Stage::Done )
    {
        showStage( Stage::Verify );
    }
}
