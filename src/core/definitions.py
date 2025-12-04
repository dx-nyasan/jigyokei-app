
# Consolidated Schema Definitions for Jigyokei Application
# This file serves as the Single Source of Truth (SSOT) for data definitions.

SCHEMA_DEFINITIONS = {
    "1_basic_info": {
        "section_id": "1_basic_info",
        "section_name": "表紙 / 1. 名称等",
        "source_reference": "申請情報入力（表紙１. 名称）.pdf, スクリーンショット(190514, 190540, 190441)",
        "ui_structure": {
            "cover_page": {
                "label": "表紙",
                "fields": {
                    "application_destination": { "label": "申請先", "type": "text_display", "value_fixed": "近畿経済産業局長", "note": "自動判定により表示 [cite: 124]" },
                    "address_zip": { "label": "郵便番号", "type": "text_display", "value_example": "641-0054", "note": "本社登記住所から自動反映 [cite: 127]" },
                    "address_pref": { "label": "都道府県", "type": "text_display", "value_example": "和歌山県" },
                    "address_city": { "label": "市区町村", "type": "text_display", "value_example": "和歌山市" },
                    "address_street": { "label": "住所（字・番地等）", "type": "text_input", "required": True, "value_example": "塩屋4丁目6番58号", "error_message_ref": "本社登記されている住所を入力してください [cite: 133]" },
                    "address_building": { "label": "マンション名等", "type": "text_input", "required": False }
                }
            },
            "applicant_details": {
                "label": "1. 名称等",
                "fields": {
                    "applicant_type": { "label": "申請種別", "type": "radio_group", "options": ["法人", "個人事業主"], "required": True, "selected_value": "法人" },
                    "corporate_name": { "label": "事業者の氏名又は名称", "type": "text_input", "required": True, "value_example": "株式会社美麗書院", "validation_rule": "正式名称を入力 [cite: 146]" },
                    "corporate_name_kana": { "label": "事業者の氏名又は名称（フリガナ）", "type": "text_input", "required": True, "validation_rule": "全角カタカナ、全角長音、全角スペース、「・」等のみ使用可 [cite: 175]", "error_scenario": "未入力または不正文字の場合、赤枠で警告表示" },
                    "representative_title": { "label": "代表者の役職", "type": "text_input", "required": True, "placeholder": "代表取締役", "note": "個人事業主の場合は「代表」と入力 [cite: 178]" },
                    "representative_name": { "label": "代表者の氏名", "type": "text_input", "required": True, "value_example": "北原 千恵", "validation_rule": "氏名の間には、全角スペースを1文字分入れること [cite: 180]" },
                    "capital": { "label": "資本金又は出資の額", "type": "number_input", "unit": "円", "required": True, "validation_rule": "半角数字 [cite: 189]" },
                    "employees": { "label": "常時使用する従業員の数", "type": "number_input", "unit": "人", "required": True, "validation_rule": "半角数字 [cite: 201]" },
                    "industry": { "label": "業種", "type": "cascading_dropdown", "required": True, "levels": [ { "name": "major", "label": "大分類", "selected_value": "D 建設業", "options_sample": ["A 農業", "D 建設業", "R サービス業..."] }, { "name": "middle", "label": "中分類", "selected_value": "06 総合工事業", "options_sample": ["06 総合工事業", "07 職別工事業", "08 設備工事業"] }, { "name": "minor", "label": "小分類", "selected_value": "--なし--", "note": "選択肢が「なし」のみの場合は中分類までで可 [cite: 212]" }, { "name": "detail", "label": "細分類", "selected_value": "--なし--" } ] },
                    "corporate_number": { "label": "法人番号", "type": "text_display", "value_example": "4170001013831", "note": "gBizIDより自動取得、編集不可 [cite: 220]" },
                    "establishment_date": { "label": "設立年月日", "type": "date_picker", "required": True, "format": "YYYY/MM/DD", "input_method": "カレンダーアイコン選択または直接入力 [cite: 223]" }
                }
            }
        }
    },
    "2_goals_and_assumptions": {
        "section_id": "2_goals_and_assumptions",
        "section_name": "2. 事業継続力強化の目標",
        "source_reference": "02申請情報入力（２. 目標）.pdf, 02-01～02-06tebiki_tandoku.pdf",
        "ui_structure": {
            "business_overview_section": {
                "label": "自社の事業活動の概要",
                "fields": {
                    "business_overview": {
                        "label": "自社の事業活動の概要",
                        "type": "textarea",
                        "required": True,
                        "validation_rule": "以下の要素が必須:\n1. 誰に・何を・どのように提供しているか\n2. サプライチェーンにおける役割、または地域経済における役割 (認定要件) [cite: 02-02]",
                        "note": "記入例: 「当社は○○地域において、××を製造し、△△へ納品している。地域唯一の××サプライヤーとして...」",
                        "value_example": "当社は和歌山県内において、公共土木工事（道路・河川等）および民間建築工事を主力事業とする建設業者である。\n【サプライチェーン上の役割】\n平時は地域の生活基盤（インフラ）の整備・維持管理を担っている。災害時においては、自治体との防災協定に基づき、道路の啓開（ガレキ撤去）や堤防の応急復旧など、地域復旧活動の最前線を担う役割がある。また、地元の協力会社（重機オペレーター等）への発注責任も有している。"
                    }
                }
            },
            "business_purpose_section": {
                "label": "事業継続力強化に取り組む目的",
                "fields": {
                    "business_purpose": {
                        "label": "事業継続力強化に取り組む目的",
                        "type": "textarea",
                        "required": True,
                        "note": "推奨される観点 [cite: 02-03]:\n- 人命の安全確保\n- 供給責任の完遂\n- 地域社会からの信頼維持",
                        "value_example": "1. 【人命優先】従業員とその家族、および協力会社作業員の命を守ることを最優先とする。\n2. 【地域貢献】災害発生時において、地域のインフラ（道路、河川等）の応急復旧を担う建設業としての社会的責任を果たす。\n3. 【信用維持】工期の遅れを最小限に抑え、発注者からの信頼を維持し、事業を継続させる。"
                    }
                }
            },
            "disaster_assumption_section": {
                "label": "事業活動に影響を与える自然災害等の想定",
                "fields": {
                    "disaster_assumption": {
                        "label": "想定する自然災害等",
                        "type": "text_input",
                        "required": True,
                        "note": "ハザードマップ (J-SHIS, 重ねるハザードマップ等) を確認の上、自社拠点に影響がある災害を記載すること [cite: 02-04, 02-05]",
                        "value_example": "和歌山市ハザードマップおよびJ-SHISを確認した結果、当社の事業所は「南海トラフ地震」による最大震度6強の揺れ、および津波浸水想定区域（浸水深2m未満）に該当するため、これを想定災害とする。"
                    }
                }
            },
            "impact_assessment_section": {
                "label": "自然災害等の発生が事業活動に与える影響",
                "fields": {
                    "impact_list": {
                        "label": "影響リスト",
                        "type": "list_composite",
                        "required": True,
                        "note": "1つの災害想定に対し、5つの観点で記述する [cite: 02-06]",
                        "sub_fields": {
                            "disaster_type": { 
                                "label": "想定する自然災害等", 
                                "type": "text_input", 
                                "required": True,
                                "value_example": "南海トラフ地震（震度6強）および津波"
                            },
                            "impact_personnel": { 
                                "label": "人員に関する影響", 
                                "type": "textarea", 
                                "required": True,
                                "value_example": "発災直後の混乱および交通網の寸断により、従業員の3割が出社・参集不能となる。また、現場作業員の負傷リスクがある。"
                            },
                            "impact_building": { 
                                "label": "建物・設備に関する影響", 
                                "type": "textarea", 
                                "required": True,
                                "value_example": "本社事務所の停電、什器の転倒。沿岸部の資材置き場における重機・車両の水没故障。"
                            },
                            "impact_funds": { 
                                "label": "資金繰りに関する影響", 
                                "type": "textarea", 
                                "required": True,
                                "value_example": "工事中断による出来高入金の遅延（1～2ヶ月）。重機の修理・買い替え費用および事務所復旧費用の発生により、運転資金が一時的に逼迫する。"
                            },
                            "impact_info": { 
                                "label": "情報に関する影響", 
                                "type": "textarea", 
                                "required": True,
                                "value_example": "本社サーバーの破損による財務データ、工事図面、工程表データの消失・閲覧不能。"
                            },
                            "impact_other": { 
                                "label": "その他の影響", 
                                "type": "textarea", 
                                "required": False,
                                "value_example": "燃料（軽油）および建設資材（生コン、砕石）の供給ストップによる工期の大幅な遅延。"
                            }
                        }
                    }
                }
            }
        }
    },
    "3_1_response_procedures": {
        "section_id": "3_1_response_procedures",
        "section_name": "3. 事業継続力強化の内容（1）自然災害等が発生した場合における対応手順",
        "source_reference": "03申請情報入力（３. 内容（1））.pdf, 03-01～03-04tebiki_tandoku.pdf",
        "ui_structure": {
            "response_table": {
                "label": "対応手順テーブル",
                "type": "fixed_table",
                "rows": [
                    {
                        "category": "人命の安全確保",
                        "guidance_ref": "03-02",
                        "fields": {
                            "action_content": {
                                "label": "初動対応の内容",
                                "type": "textarea",
                                "required": True,
                                "value_example": "作業の手を止め、重機・車両のエンジンを停止し、安全な場所（高台等）へ避難する。併せて、全従業員および協力会社作業員の点呼を行う。"
                            },
                            "timing": {
                                "label": "発災後の対応時期",
                                "type": "dropdown",
                                "required": True,
                                "options": ["発災直後", "発災後１時間以内", "発災後３時間以内", "発災後６時間以内", "発災後１２時間以内", "発災後２４時間以内", "発災後３日以内", "発災後１週間以内", "国内感染者発生後", "社内感染者発生後", "その他"],
                                "value_example": "発災直後"
                            },
                            "preparation_content": {
                                "label": "事前対策の内容",
                                "type": "textarea",
                                "required": True,
                                "value_example": "避難訓練の実施（年1回）、ハザードマップによる避難場所の周知、ヘルメット・防災グッズの各現場への配備。"
                            }
                        }
                    },
                    {
                        "category": "非常時の緊急時体制の構築",
                        "guidance_ref": "03-03",
                        "fields": {
                            "action_content": {
                                "label": "初動対応の内容",
                                "type": "textarea",
                                "required": True,
                                "value_example": "代表取締役を本部長とする災害対策本部を本社に設置する。現場代理人は現場の状況を本部に報告する。"
                            },
                            "timing": {
                                "label": "発災後の対応時期",
                                "type": "dropdown",
                                "required": True,
                                "options": ["発災直後", "発災後１時間以内", "発災後３時間以内", "発災後６時間以内", "発災後１２時間以内", "発災後２４時間以内", "発災後３日以内", "発災後１週間以内", "国内感染者発生後", "社内感染者発生後", "その他"],
                                "value_example": "発災後１時間以内"
                            },
                            "preparation_content": {
                                "label": "事前対策の内容",
                                "type": "textarea",
                                "required": True,
                                "value_example": "緊急連絡網（協力会社含む）の整備・更新、BCP発動基準（震度6弱以上等）の策定。"
                            }
                        }
                    },
                    {
                        "category": "被害状況の把握・被害情報の共有",
                        "guidance_ref": "03-04",
                        "fields": {
                            "action_content": {
                                "label": "初動対応の内容",
                                "type": "textarea",
                                "required": True,
                                "value_example": "現場代理人は現場の被害状況（人的被害、足場の倒壊、重機の破損等）を確認し、写真とともに本社へ報告する。"
                            },
                            "timing": {
                                "label": "発災後の対応時期",
                                "type": "dropdown",
                                "required": True,
                                "options": ["発災直後", "発災後１時間以内", "発災後３時間以内", "発災後６時間以内", "発災後１２時間以内", "発災後２４時間以内", "発災後３日以内", "発災後１週間以内", "国内感染者発生後", "社内感染者発生後", "その他"],
                                "value_example": "発災後１２時間以内"
                            },
                            "preparation_content": {
                                "label": "事前対策の内容",
                                "type": "textarea",
                                "required": True,
                                "value_example": "現場における被害確認チェックリストの作成、スマートフォンを活用した画像報告ルールの周知。"
                            }
                        }
                    },
                    {
                        "category": "その他の取組",
                        "guidance_ref": "地域貢献等",
                        "fields": {
                            "action_content": {
                                "label": "初動対応の内容",
                                "type": "textarea",
                                "required": False,
                                "value_example": "自治体からの要請に基づき、道路啓開や応急復旧工事への出動準備を行う。近隣住民の救助活動に協力する。"
                            },
                            "timing": {
                                "label": "発災後の対応時期",
                                "type": "dropdown",
                                "required": False,
                                "options": ["発災直後", "発災後１時間以内", "発災後３時間以内", "発災後６時間以内", "発災後１２時間以内", "発災後２４時間以内", "発災後３日以内", "発災後１週間以内", "国内感染者発生後", "社内感染者発生後", "その他"],
                                "value_example": "発災後１２時間以内"
                            },
                            "preparation_content": {
                                "label": "事前対策の内容",
                                "type": "textarea",
                                "required": False,
                                "value_example": "自治体との防災協定の締結、資機材（重機、発電機等）のメンテナンスと燃料備蓄。"
                            }
                        }
                    }
                ]
            }
        }
    },
    "integrated_measures_funds": {
        "section_id": "integrated_measures_funds",
        "section_name": "3. 対策・設備 & 5. 資金",
        "source_reference": "04申請情報入力, 04-01tebiki, 04-02tebiki",
        "ui_structure": {
            "measures_section": {
                "label": "3. (2) 事業継続力強化に資する対策及び取組",
                "type": "fixed_table",
                "rows": [
                    {
                        "category": "A.人員体制の整備",
                        "fields": {
                            "current_measure": { "label": "現在の取組", "type": "textarea", "required": True, "value_example": "・現在、具体的な対策は行っていない。" },
                            "future_plan": { "label": "今後の計画", "type": "textarea", "required": True, "value_example": "・事業所から10km圏内に居住する従業員を緊急参集担当に任命する。" }
                        }
                    },
                    {
                        "category": "B.設備・機器の導入",
                        "fields": {
                            "current_measure": { "label": "現在の取組", "type": "textarea", "required": True, "value_example": "・本社工場の耐震補強済み。" },
                            "future_plan": { 
                                "label": "今後の計画", 
                                "type": "textarea", 
                                "required": True, 
                                "value_example": "・停電時の事業継続のため、非常用LPガス発電機を本社および主要現場に導入する。",
                                "validation_rule": "税制優遇を受ける場合、ここにその設備について記載すること。"
                            }
                        }
                    },
                    {
                        "category": "C.資金の確保",
                        "fields": {
                            "current_measure": { "label": "現在の取組", "type": "textarea", "required": True, "value_example": "・損害保険（火災・地震）への加入。" },
                            "future_plan": { "label": "今後の計画", "type": "textarea", "required": True, "value_example": "・事業中断保険（利益補償）への追加加入検討。" }
                        }
                    },
                    {
                        "category": "D.重要情報の保護",
                        "fields": {
                            "current_measure": { "label": "現在の取組", "type": "textarea", "required": True, "value_example": "・財務データの定期的な外付けHDDバックアップ。" },
                            "future_plan": { "label": "今後の計画", "type": "textarea", "required": True, "value_example": "・クラウドストレージの導入によるデータ遠隔地保全。" }
                        }
                    }
                ]
            },
            "equipment_section": {
                "label": "3. (3) 事業継続力強化設備等の種類（税制優遇）",
                "fields": {
                    "use_tax_incentive": {
                        "label": "税制優遇措置を活用する",
                        "type": "checkbox",
                        "value_example": True
                    },
                    "equipment_list": {
                        "label": "設備リスト",
                        "type": "dynamic_table",
                        "condition": "use_tax_incentive == True",
                        "fields": {
                            "name_model": { "label": "設備等の名称/型式", "type": "text_input", "required": True, "value_example": "非常用LPガス発電機 (G-Force 5000)" },
                            "acquisition_date": { "label": "取得年月", "type": "date_month", "required": True, "value_example": "2025/08" },
                            "location": { "label": "所在地", "type": "text_input", "required": True, "value_example": "本社工場（屋上設置）" },
                            "unit_price": { "label": "単価", "type": "currency", "required": True, "value_example": "2,500,000" },
                            "quantity": { "label": "数量", "type": "number", "required": True, "value_example": "1" },
                            "amount": { "label": "金額", "type": "currency", "required": True, "value_example": "2,500,000", "validation_rule": "単価 × 数量" }
                        }
                    },
                    "compliance_checks": {
                        "label": "確認事項",
                        "type": "checkbox_group",
                        "condition": "use_tax_incentive == True",
                        "options": [
                            "建築基準法・消防法義務ではない",
                            "中古品・貸付資産ではない",
                            "補助金交付を受けていない"
                        ],
                        "required": True,
                        "value_example": "All Checked"
                    }
                }
            },
            "funds_section": {
                "label": "5. 事業継続力強化を実施するために必要な資金の額及びその調達方法",
                "type": "dynamic_table",
                "fields": {
                    "item": { "label": "実施事項", "type": "text_input", "required": True, "value_example": "非常用発電機の導入" },
                    "usage": { "label": "使途・用途", "type": "text_input", "required": True, "value_example": "設備購入費および設置工事費" },
                    "method": { "label": "資金調達方法", "type": "text_input", "required": True, "value_example": "自己資金" },
                    "amount": { 
                        "label": "金額", 
                        "type": "currency", 
                        "required": True, 
                        "value_example": "2,500,000",
                        "validation_rule": "合計額は、Section 3-3の設備投資額やその他の対策費用と整合していること。"
                    }
                }
            }
        }
    },
    "4_5_cooperation_pdca": {
        "section_id": "4_5_cooperation_pdca",
        "section_name": "4. 協力体制 & 5. PDCA",
        "source_reference": "04協力体制.pdf, 05PDCA.pdf",
        "ui_structure": {
            "cooperation_section": {
                "label": "4. 事業継続力強化の実施に協力する者の名称等",
                "type": "fixed_table",
                "rows": [
                    {
                        "category": "協力者1",
                        "fields": {
                            "name": { "label": "名称", "type": "text_input", "required": False, "value_example": "A株式会社" },
                            "address": { "label": "住所", "type": "text_input", "required": False, "value_example": "○○県○○市○○町○－○" },
                            "representative": { "label": "代表者の氏名", "type": "text_input", "required": False, "value_example": "○○ ○○" },
                            "content": { "label": "協力の内容", "type": "textarea", "required": False, "value_example": "自然災害に備えた事前対策の取組強化について、技術的な助言を受けるほか、自社の生産設備に支障が生じた場合、同社の生産設備を借りて、代替生産を行うことについて、検討・決定する。" }
                        }
                    },
                    {
                        "category": "協力者2",
                        "fields": {
                            "name": { "label": "名称", "type": "text_input", "required": False, "value_example": "B銀行○○支店" },
                            "address": { "label": "住所", "type": "text_input", "required": False, "value_example": "○○県○○市…" },
                            "representative": { "label": "代表者の氏名", "type": "text_input", "required": False, "value_example": "○○ ○○" },
                            "content": { "label": "協力の内容", "type": "textarea", "required": False, "value_example": "被災時において、最大○○万円までの緊急融資を受けられる契約を結んでおくとともに、○○県信用保証協会のセーフティネット保証を活用することについて、事前に協議を行う。" }
                        }
                    },
                    {
                        "category": "協力者3",
                        "fields": {
                            "name": { "label": "名称", "type": "text_input", "required": False, "value_example": "C商工会議所" },
                            "address": { "label": "住所", "type": "text_input", "required": False, "value_example": "○○県○○市…" },
                            "representative": { "label": "代表者の氏名", "type": "text_input", "required": False, "value_example": "○○ ○○" },
                            "content": { "label": "協力の内容", "type": "textarea", "required": False, "value_example": "○水災\n・大規模な水害の発生が見込まれる際、注意喚起を依頼する。\n・水害に対する事業継続の強化に関する指導を依頼する。\n○感染症\n・行政の支援策の概要や申請手続きについて情報提供を依頼する。" }
                        }
                    },
                    {
                        "category": "協力者4",
                        "fields": {
                            "name": { "label": "名称", "type": "text_input", "required": False, "value_example": "D保険代理店" },
                            "address": { "label": "住所", "type": "text_input", "required": False, "value_example": "○○県○○市…" },
                            "representative": { "label": "代表者の氏名", "type": "text_input", "required": False, "value_example": "○○ ○○" },
                            "content": { "label": "協力の内容", "type": "textarea", "required": False, "value_example": "・サイバー攻撃に対する適切なリスク対策の指導等" }
                        }
                    }
                ]
            },
            "pdca_section": {
                "label": "5. 平時の推進体制の整備、訓練及び教育の実施その他の事業継続力強化の実効性を確保するための取組",
                "fields": {
                    "management_system": {
                        "label": "平時の推進体制の整備",
                        "type": "textarea",
                        "required": True,
                        "value_example": "・代表取締役の指揮の下、○○部を統括として本計画の推進体制を整備。\n・社内の管理職全員で組織する「防災・減災対策会議」（年2回開催）において、具体的な取組を検討・決定する。"
                    },
                    "training_education": {
                        "label": "訓練・教育の実施",
                        "type": "textarea",
                        "required": True,
                        "value_example": "・毎年5月を目処に、全従業員参加の教育・訓練を実施する。\n・毎年2月頃に経営層の指導の下、全従業員参加の感染症のセミナーを実施するとともに、従業員が感染した場合を想定した訓練（平時からの時差出勤やテレワーク等）を年1回実施する。"
                    },
                    "plan_review": {
                        "label": "計画の見直し",
                        "type": "textarea",
                        "required": True,
                        "value_example": "・訓練結果等を踏まえ実態に則した計画となるように、年1回以上計画の見直しを実行する。"
                    }
                }
            }
        }
    },
    "attachments_checklist": {
        "section_id": "attachments_checklist",
        "section_name": "添付書類 & チェックシート",
        "source_reference": "06申請情報入力（添付書類）.pdf, 07申請情報入力（チェックシート）.pdf",
        "ui_structure": {
            "attachments_section": {
                "label": "4. 添付書類",
                "fields": {
                    "check_sheet": { "label": "事業継続力強化計画チェックシート", "type": "file_upload", "required": False, "note": "必須添付とあるが、システム上は任意（資料05参照）。テンプレートは以下よりダウンロード [中小企業庁HP](https://www.chusho.meti.go.jp/keiei/antei/bousai/list.html)" },
                    "financial_risk": { "label": "財務リスク評価シート", "type": "file_upload", "required": False, "note": "任意（推奨）" },
                    "existing_bcp": { "label": "既存のBCP等", "type": "file_upload", "required": False, "note": "既に策定済みの場合" },
                    "other_docs": { "label": "その他添付資料", "type": "file_upload", "required": False, "note": "必要に応じて添付" }
                }
            },
            "checklist_section": {
                "label": "5. チェックシート・誓約",
                "fields": {
                    "certification_compliance": { 
                        "label": "認定要件への適合", 
                        "text": "申請内容が認定要件に適合していること", 
                        "type": "checkbox", 
                        "required": True, 
                        "validation_rule": "Must be Checked" 
                    },
                    "no_false_statements": { 
                        "label": "虚偽記載の不存在", 
                        "text": "申請内容に虚偽がないこと", 
                        "type": "checkbox", 
                        "required": True, 
                        "validation_rule": "Must be Checked" 
                    },
                    "not_anti_social": { 
                        "label": "反社会的勢力非該当", 
                        "text": "反社会的勢力に該当しないこと", 
                        "type": "checkbox", 
                        "required": True, 
                        "validation_rule": "Must be Checked" 
                    },
                    "not_cancellation_subject": { 
                        "label": "取消事由非該当", 
                        "text": "認定の取消し事由に該当しないこと", 
                        "type": "checkbox", 
                        "required": True, 
                        "validation_rule": "Must be Checked" 
                    },
                    "legal_compliance": { 
                        "label": "関係法令の遵守", 
                        "text": "私的独占禁止法、下請法、その他関係法令に抵触しないことへの誓約。", 
                        "type": "checkbox", 
                        "required": True, 
                        "validation_rule": "Must be Checked" 
                    },
                    "sme_requirements": { 
                        "label": "中小事業者の要件", 
                        "text": "個人事業主は開業届提出済み、法人は登記済みであること。", 
                        "type": "checkbox", 
                        "required": True, 
                        "validation_rule": "Must be Checked" 
                    },
                    "registration_consistency": {
                        "label": "登記情報との一致確認",
                        "text": "申請書に記載された事業者の名称・代表者の氏名は、登記上の本店所在地...",
                        "type": "checkbox",
                        "required": True,
                        "note": "[gBizINFO](https://info.gbiz.go.jp/) 等で最新情報を確認のこと",
                        "validation_rule": "Must be Checked"
                    },
                    "data_utilization_consent": { 
                        "label": "データ利活用への同意", 
                        "text": "「経済産業省関係補助金等に係るデータの取扱いに関する利用規約」の内容を確認し...",
                        "type": "dropdown", 
                        "options": ["可", "不可"], 
                        "required": True, 
                        "note": "[利用規約](https://www.chusho.meti.go.jp/hojyokin/data_policy/) を確認",
                        "validation_rule": "Must Select" 
                    },
                    "case_publication_consent": { 
                        "label": "事例公表への同意", 
                        "type": "dropdown", 
                        "options": ["可", "不可"], 
                        "required": True, 
                        "validation_rule": "Must Select" 
                    }
                }
            }
        }
    }
}
