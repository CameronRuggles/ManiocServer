/* === OnionHost OS ===
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "OnionHostGuardViewStep.h"

#include "GlobalStorage.h"
#include "JobQueue.h"
#include "utils/Logger.h"

#include <QCheckBox>
#include <QLabel>
#include <QStackedWidget>
#include <QVBoxLayout>

CALAMARES_PLUGIN_FACTORY_DEFINITION( OnionHostGuardViewStepFactory,
                                     registerPlugin< OnionHostGuardViewStep >(); )

namespace
{

QLabel*
makeTitle( const QString& text )
{
    auto* label = new QLabel( text );
    QFont f = label->font();
    f.setPointSize( 22 );
    f.setBold( true );
    label->setFont( f );
    label->setWordWrap( true );
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

Calamares::GlobalStorage*
gs()
{
    return Calamares::JobQueue::instance()->globalStorage();
}

}  // namespace

OnionHostGuardViewStep::Decision
OnionHostGuardViewStep::guardDecision( const QString& installChoice,
                                       const QString& storedPassphrase,
                                       const QString& generatedPhrase )
{
    if ( installChoice == QStringLiteral( "manual" ) )
    {
        return Decision::Manual;
    }
    if ( !generatedPhrase.isEmpty() && storedPassphrase == generatedPhrase )
    {
        return Decision::Pass;
    }
    return Decision::Block;
}

OnionHostGuardViewStep::OnionHostGuardViewStep( QObject* parent )
    : Calamares::ViewStep( parent )
{
    buildUi();
    emit nextStatusChanged( false );
}

OnionHostGuardViewStep::~OnionHostGuardViewStep()
{
    if ( m_widget && m_widget->parent() == nullptr )
    {
        m_widget->deleteLater();
    }
}

QString
OnionHostGuardViewStep::prettyName() const
{
    return tr( "Encryption check", "@label" );
}

QWidget*
OnionHostGuardViewStep::widget()
{
    return m_widget;
}

bool
OnionHostGuardViewStep::isNextEnabled() const
{
    switch ( m_decision )
    {
    case Decision::Pass:
        return true;
    case Decision::Manual:
        return m_manualAck && m_manualAck->isChecked();
    case Decision::Block:
    default:
        return false;
    }
}

bool
OnionHostGuardViewStep::isBackEnabled() const
{
    return true;
}

bool
OnionHostGuardViewStep::isAtBeginning() const
{
    return true;
}

bool
OnionHostGuardViewStep::isAtEnd() const
{
    return true;
}

Calamares::JobList
OnionHostGuardViewStep::jobs() const
{
    return Calamares::JobList();
}

void
OnionHostGuardViewStep::buildUi()
{
    m_widget = new QWidget;
    auto* mainLayout = new QVBoxLayout( m_widget );
    mainLayout->setContentsMargins( 30, 22, 30, 10 );
    m_stack = new QStackedWidget;
    mainLayout->addWidget( m_stack );
    mainLayout->addStretch();

    // --- Pass page (index 0) ---------------------------------------
    auto* passPage = new QWidget;
    auto* passLayout = new QVBoxLayout( passPage );
    passLayout->setContentsMargins( 0, 6, 0, 0 );
    passLayout->addWidget( makeTitle( tr( "Encryption is on", "@title" ) ) );
    passLayout->addWidget( makeBody(
        tr( "This computer will be installed with its disk "
            "encrypted. The key is the 7 words from the passphrase "
            "page - keep that paper somewhere safe.\n\n"
            "There is nothing to fill in here. Press Next to "
            "continue.",
            "@body" ) ) );
    passLayout->addStretch();
    m_stack->addWidget( passPage );

    // --- Block page (index 1) ---------------------------------------
    auto* blockPage = new QWidget;
    auto* blockLayout = new QVBoxLayout( blockPage );
    blockLayout->setContentsMargins( 0, 6, 0, 0 );
    blockLayout->addWidget(
        makeTitle( tr( "Encryption isn't on yet", "@title" ) ) );
    blockLayout->addWidget( makeBody(
        tr( "This computer is never installed without encryption, "
            "so setup has stopped here - before anything was "
            "written to the disk.\n\n"
            "Go back one page. On the Partitions page, choose "
            "\"Erase disk\". The \"Encrypt system\" box is already "
            "ticked for you, and there are no passphrase boxes to "
            "fill in - the 7 words from the passphrase page do the "
            "locking on their own.\n\n"
            "Your paper copy is still the right one: going back "
            "does not make new words.",
            "@body" ) ) );
    blockLayout->addStretch();
    m_stack->addWidget( blockPage );

    // --- Manual page (index 2) --------------------------------------
    auto* manualPage = new QWidget;
    auto* manualLayout = new QVBoxLayout( manualPage );
    manualLayout->setContentsMargins( 0, 6, 0, 0 );
    manualLayout->addWidget(
        makeTitle( tr( "Check your partitions", "@title" ) ) );
    manualLayout->addWidget( makeBody(
        tr( "You laid out the partitions yourself, so this check "
            "cannot see them automatically.\n\n"
            "This computer is only ever installed fully encrypted. "
            "Continue only if BOTH of these are true:\n\n"
            "- the partition that will hold the system is encrypted "
            "(its type is LUKS), and\n"
            "- the passphrase you gave that partition is the 7 words "
            "from the passphrase page, exactly as written.\n\n"
            "The installer checks again before it finishes. If the "
            "check fails, the installation stops.",
            "@body" ) ) );
    m_manualAck = new QCheckBox(
        tr( "Yes - encrypted (LUKS), with the 7-word passphrase.",
            "@checkbox" ) );
    {
        QFont f = m_manualAck->font();
        f.setPointSize( 12 );
        m_manualAck->setFont( f );
    }
    connect( m_manualAck, &QCheckBox::toggled, this,
             [ this ]() { emit nextStatusChanged( isNextEnabled() ); } );
    manualLayout->addWidget( m_manualAck );
    manualLayout->addStretch();
    m_stack->addWidget( manualPage );

    // --- No-phrase page (index 3) -----------------------------------
    auto* noPhrasePage = new QWidget;
    auto* noPhraseLayout = new QVBoxLayout( noPhrasePage );
    noPhraseLayout->setContentsMargins( 0, 6, 0, 0 );
    noPhraseLayout->addWidget(
        makeTitle( tr( "Something went wrong", "@title" ) ) );
    noPhraseLayout->addWidget( makeBody(
        tr( "The disk passphrase step did not run, so there is no "
            "passphrase to lock this computer with, and setup "
            "cannot continue.\n\n"
            "Close the installer and start it again. If this keeps "
            "happening, the installation disc or USB stick may be "
            "damaged - make a fresh one and try again.",
            "@body" ) ) );
    noPhraseLayout->addStretch();
    m_stack->addWidget( noPhrasePage );
}

void
OnionHostGuardViewStep::evaluate()
{
    auto* storage = gs();
    QString choice;
    const QVariant choices = storage->value( QStringLiteral( "partitionChoices" ) );
    if ( choices.isValid() )
    {
        choice = choices.toMap().value( QStringLiteral( "install" ) ).toString();
    }
    const QString stored = storage->value( QStringLiteral( "luksPassphrase" ) ).toString();
    const QString generated
        = storage->value( QStringLiteral( "onionhostGeneratedPhrase" ) ).toString();
    m_phraseMissing = generated.isEmpty();
    m_decision = guardDecision( choice, stored, generated );
    cDebug() << "OnionHostGuard: choice" << choice << "decision"
             << static_cast< int >( m_decision ) << "phraseMissing" << m_phraseMissing;
    switch ( m_decision )
    {
    case Decision::Pass:
        m_stack->setCurrentIndex( 0 );
        break;
    case Decision::Manual:
        m_stack->setCurrentIndex( 2 );
        break;
    case Decision::Block:
    default:
        m_stack->setCurrentIndex( m_phraseMissing ? 3 : 1 );
        break;
    }
    emit nextStatusChanged( isNextEnabled() );
}

void
OnionHostGuardViewStep::onActivate()
{
    evaluate();
}
