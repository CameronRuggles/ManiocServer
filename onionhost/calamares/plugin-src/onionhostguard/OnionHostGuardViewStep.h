/* === OnionHost OS ===
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 * Encryption guard page (slice 5A; FIX-BRIEF-ENCRYPTION-GUARD).
 *
 * Sequenced immediately after the stock partition page. By the
 * time this step activates, the partition page has left
 * GlobalStorage "luksPassphrase" holding the passphrase the layout
 * was queued with (obscured), and the partition module's Config
 * has recorded the chosen mode in "partitionChoices". This step
 * compares the stored passphrase against the generated phrase
 * ("onionhostGeneratedPhrase", also obscured - the transform is
 * deterministic, so equality of the obscured forms is equality of
 * the phrases):
 *
 *   - automated modes (erase / replace / alongside): PASS only on
 *     an exact match. Anything else (empty after an unticked
 *     checkbox, a value typed into the partition page's fields)
 *     BLOCKS advancing with plain-language recovery instructions:
 *     the install is stopped here, before any partition is
 *     written, instead of ten minutes later at onionhostbootkey.
 *   - manual partitioning: the pending layout is not visible from
 *     GlobalStorage in the show phase, so the page explains what a
 *     valid manual layout is and asks the user to confirm it;
 *     onionhostbootkey remains the hard verifier in the exec phase.
 *
 * This step is a backstop. The primary mechanism is the patched
 * partition module (patches/0001-onionhost-force-encryption),
 * which queues automated layouts with the generated phrase by
 * construction; in the shipped flow this page normally just shows
 * a short "encryption is on" confirmation.
 */

#ifndef ONIONHOSTGUARDVIEWSTEP_H
#define ONIONHOSTGUARDVIEWSTEP_H

#include "utils/PluginFactory.h"
#include "viewpages/ViewStep.h"

#include <QObject>
#include <QString>

class QCheckBox;
class QStackedWidget;
class QWidget;

class OnionHostGuardViewStep : public Calamares::ViewStep
{
    Q_OBJECT

public:
    enum class Decision
    {
        Pass,
        Block,
        Manual
    };

    /// @brief The guard's decision as a pure function of the
    /// GlobalStorage values, so it can be unit-tested without the
    /// full installer. @p storedPassphrase and @p generatedPhrase
    /// are the obscured GlobalStorage forms; equality is exact.
    static Decision guardDecision( const QString& installChoice,
                                   const QString& storedPassphrase,
                                   const QString& generatedPhrase );

    explicit OnionHostGuardViewStep( QObject* parent = nullptr );
    ~OnionHostGuardViewStep() override;

    QString prettyName() const override;
    QWidget* widget() override;

    bool isNextEnabled() const override;
    bool isBackEnabled() const override;
    bool isAtBeginning() const override;
    bool isAtEnd() const override;

    void onActivate() override;

    Calamares::JobList jobs() const override;

private:
    void buildUi();
    void evaluate();

    Decision m_decision = Decision::Block;
    bool m_phraseMissing = false;

    QWidget* m_widget = nullptr;
    QStackedWidget* m_stack = nullptr;
    QCheckBox* m_manualAck = nullptr;
};

CALAMARES_PLUGIN_FACTORY_DECLARATION( OnionHostGuardViewStepFactory )

#endif  // ONIONHOSTGUARDVIEWSTEP_H
